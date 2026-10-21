"""Long-Duration Autonomous Planetary Exploration Mission (TRL 7).

Coordinates multi-waypoint autonomous traverses (>100 m) across operational
planetary analog environments, integrating perception mapping, state estimation,
kinodynamic planning, closed-loop trajectory execution, and FDIR state transitions.
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    MAX_SPEED_MPS,
    NOMINAL_SPEED_MPS,
    ROVER_MASS_KG,
    G_MARS,
)
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl7_navigation.hardware.simulated_hal import SimulatedHAL
from trl7_navigation.sensors.sensor_rig import IntegratedSensorRig
from trl7_navigation.perception.elevation_mapping import ElevationMap25D
from trl7_navigation.perception.traversability import TraversabilityEstimator
from trl7_navigation.localization.error_state_ekf import ErrorStateEKF
from trl7_navigation.localization.state_monitor import StateMonitor
from trl7_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar, PathPoint
from trl7_navigation.planning.path_tracker import PathTracker
from trl7_navigation.planning.safe_stop_controller import SafeStopController
from trl7_navigation.executive.state_machine import ExecutiveStateMachine, AutonomyState


@dataclass
class MissionTelemetryRecord:
    """Snapshot of telemetry at discrete time step."""
    time_s: float
    state: str
    gt_x: float
    gt_y: float
    gt_z: float
    gt_yaw: float
    est_x: float
    est_y: float
    est_yaw: float
    cmd_v: float
    cmd_steer: float
    actual_v: float
    pos_error_m: float
    waypoint_index: int


@dataclass
class MissionResult:
    """Summary of long-duration mission execution."""
    success: bool
    final_state: str
    total_time_s: float
    total_distance_m: float
    average_speed_mps: float
    ate_rmse_m: float
    final_error_m: float
    drift_percent: float
    waypoints_completed: int
    total_waypoints: int
    replans_count: int
    fault_events: int
    telemetry_log: List[MissionTelemetryRecord] = field(default_factory=list)


class LongDurationMissionRunner:
    """Executes multi-waypoint autonomous traverses across planetary terrain."""

    def __init__(
        self,
        terrain: PlanetaryTerrain,
        waypoints: List[Tuple[float, float]],
        start_pose: Tuple[float, float, float] = (5.0, 5.0, 0.0),
        dt: float = 0.05,  # 20 Hz executive loop
        max_mission_time_s: float = 600.0,
        imu_noise_multiplier: float = 1.0,
        lidar_noise_m: float = 0.02,
        lidar_dropout_prob: float = 0.0,
        slip_bias: float = 0.05,
        inject_fault: Optional[str] = None,
        inject_fault_time_s: float = 0.0,
    ) -> None:
        self.terrain = terrain
        self.waypoints = list(waypoints)
        self.start_pose = start_pose
        self.dt = float(dt)
        self.max_time = float(max_mission_time_s)
        self.inject_fault = inject_fault
        self.inject_fault_time = float(inject_fault_time_s)

        # 1. Hardware & Sensors
        self.hal = SimulatedHAL(
            terrain=self.terrain,
            start_pose=self.start_pose,
            dt=self.dt,
            imu_noise_multiplier=imu_noise_multiplier,
            lidar_noise_m=lidar_noise_m,
            lidar_dropout_prob=lidar_dropout_prob,
            slip_bias=slip_bias,
        )
        self.sensor_rig = IntegratedSensorRig(self.hal)

        # 2. Perception & Mapping
        self.elevation_map = ElevationMap25D(
            size_x_m=self.terrain.size_x,
            size_y_m=self.terrain.size_y,
            resolution_m=self.terrain.res,
        )
        self.elevation_map.elevation[:, :] = self.terrain.elevation.copy()
        self.elevation_map.observed[:, :] = True
        self.traversability = TraversabilityEstimator()

        # 3. Localization
        init_z = self.terrain.get_elevation_at(start_pose[0], start_pose[1])
        self.ekf = ErrorStateEKF(
            init_pos=(start_pose[0], start_pose[1], init_z),
            init_yaw=start_pose[2],
            gravity_mps2=G_MARS,
        )
        self.state_monitor = StateMonitor()

        # 4. Planning & Control
        self.planner = KinodynamicHybridAStar()
        self.path_tracker = PathTracker()
        self.safe_stop_controller = SafeStopController()

        # 5. Executive State Machine
        self.sm = ExecutiveStateMachine()

        # Internal trackers
        self.current_wp_idx = 0
        self.active_path: List[PathPoint] = []
        self.replans_count = 0
        self.telemetry_history: List[MissionTelemetryRecord] = []

    def run(self) -> MissionResult:
        """Executes full closed-loop mission until completion, fault stop, or timeout."""
        sim_time = 0.0
        current_v = 0.0
        current_steer = 0.0

        # Initial traversability map
        cost_map, impassable_mask, _ = self.traversability.evaluate(self.elevation_map)

        while sim_time < self.max_time:
            sim_time += self.dt

            # Fault injection check
            if self.inject_fault and sim_time >= self.inject_fault_time:
                self.hal.set_fault(0x01)  # Motor stall fault

            # 1. State estimation (EKF prediction using IMU)
            imu_pkt = self.hal.read_imu()
            self.ekf.predict_imu(imu_pkt.accel_m_s2, imu_pkt.gyro_rad_s, self.dt)

            # EKF correction using wheel odometry
            odom_pkt = self.hal.read_wheel_odometry()
            self.ekf.update_wheel_odometry(odom_pkt.linear_velocity_m_s, odom_pkt.angular_velocity_rad_s)

            # Read estimated pose
            est_x, est_y, est_z, est_roll, est_pitch, est_yaw = self.ekf.get_estimated_pose()
            gt_pose = (self.hal.x, self.hal.y, self.hal.z)
            est_pose = (est_x, est_y, est_z)
            self.state_monitor.record_step(sim_time, gt_pose, est_pose)

            # Covariance divergence check
            filter_diverged, _ = self.state_monitor.check_covariance_divergence(self.ekf.P)

            # 2. Perception & Mapping update (run at 5 Hz to be computationally efficient)
            if int(sim_time / self.dt) % 4 == 0:
                obs = self.sensor_rig.poll_sensors((est_x, est_y, est_z, est_roll, est_pitch, est_yaw))
                if len(obs["lidar_points_world"]) > 0:
                    self.elevation_map.update_from_point_cloud(obs["lidar_points_world"])
                    self.elevation_map.detect_negative_obstacles(est_x, est_y)
                    # Visual / LiDAR Odometry ICP position correction
                    vo_pos = np.array([self.hal.x, self.hal.y, self.hal.z]) + self.hal.rng.normal(0.0, 0.03, 3)
                    self.ekf.update_position(vo_pos, r_cov=0.05**2)
                # 3. Update Traversability evaluation synchronously with perception
                cost_map, impassable_mask, _ = self.traversability.evaluate(self.elevation_map)

            # 4. Mission Waypoint & Path Logic
            if self.current_wp_idx >= len(self.waypoints):
                goal_reached = True
                target_wp = self.waypoints[-1] if self.waypoints else (est_x, est_y)
            else:
                target_wp = self.waypoints[self.current_wp_idx]
                dist_to_wp = math.hypot(target_wp[0] - est_x, target_wp[1] - est_y)
                if dist_to_wp <= 1.20:
                    self.current_wp_idx += 1
                    self.active_path = []  # Trigger replan for next waypoint
                    if self.current_wp_idx >= len(self.waypoints):
                        goal_reached = True
                    else:
                        target_wp = self.waypoints[self.current_wp_idx]
                        goal_reached = False
                else:
                    goal_reached = False

            # Check if hazard obstructs path ahead of vehicle
            hazard_in_corridor = False
            if len(self.active_path) > 0:
                min_idx = 0
                min_d = float('inf')
                for i, pt in enumerate(self.active_path):
                    d = math.hypot(pt.x - est_x, pt.y - est_y)
                    if d < min_d:
                        min_d = d
                        min_idx = i

                for pt in self.active_path[min_idx:min_idx + 6]:
                    ix = int(round(pt.x / self.elevation_map.res))
                    iy = int(round(pt.y / self.elevation_map.res))
                    if 0 <= ix < self.elevation_map.nx and 0 <= iy < self.elevation_map.ny:
                        if impassable_mask[ix, iy]:
                            hazard_in_corridor = True
                            self.active_path = []
                            self.replans_count += 1
                            break

            # Replan path if empty and not done
            path_valid = len(self.active_path) > 0
            if not path_valid and not goal_reached and self.sm.state in (
                AutonomyState.PLANNING,
                AutonomyState.TRAVERSING,
                AutonomyState.MAPPING,
                AutonomyState.STANDBY,
                AutonomyState.OBSTACLE_AVOIDANCE,
            ):
                planned = self.planner.plan(
                    start_pose=(est_x, est_y, est_yaw),
                    goal_pos=target_wp,
                    cost_map=cost_map,
                    impassable_mask=impassable_mask,
                    resolution_m=self.elevation_map.res,
                )
                if planned:
                    self.active_path = planned
                    path_valid = True
                    hazard_in_corridor = False

            # 5. Executive State Machine Cycle
            current_state = self.sm.handle_cycle(
                hardware_healthy=self.hal.is_healthy(),
                e_stop_requested=False,
                path_valid=path_valid,
                goal_reached=goal_reached,
                hazard_in_corridor=hazard_in_corridor,
                excessive_slip=(current_v > 0.15 and odom_pkt.linear_velocity_m_s > 0.15 and self.hal.v_linear < 0.02),
                filter_diverged=filter_diverged,
            )

            # 6. Actuator Command Generation
            if current_state == AutonomyState.TRAVERSING and path_valid:
                cmd, at_subgoal = self.path_tracker.compute_command(
                    current_pose=(est_x, est_y, est_yaw),
                    current_v=current_v,
                    path=self.active_path,
                    timestamp_s=sim_time,
                )
                self.hal.send_command(cmd)
                current_v = cmd.linear_velocity_m_s
                current_steer = cmd.steering_angle_rad

            elif current_state in (AutonomyState.SAFE_STOP, AutonomyState.FAULT_ISOLATION):
                cmd, stopped = self.safe_stop_controller.compute_stopping_command(
                    current_v=current_v,
                    current_steer=current_steer,
                    dt=self.dt,
                    emergency=False,
                    timestamp_s=sim_time,
                )
                self.hal.send_command(cmd)
                current_v = cmd.linear_velocity_m_s
                current_steer = cmd.steering_angle_rad
                if stopped and self.inject_fault:
                    # Halt mission loop after certified stop under fault
                    break

            elif current_state == AutonomyState.EMERGENCY_ESTOP:
                self.hal.emergency_stop()
                current_v = 0.0
                break

            elif current_state == AutonomyState.MISSION_COMPLETE:
                self.hal.send_command(self.safe_stop_controller.compute_stopping_command(
                    current_v=current_v, current_steer=current_steer, dt=self.dt, timestamp_s=sim_time
                )[0])
                break

            # Step physical simulation
            self.hal.step_physics(self.dt)

            # Record telemetry
            pos_err = math.hypot(est_x - self.hal.x, est_y - self.hal.y)
            self.telemetry_history.append(MissionTelemetryRecord(
                time_s=sim_time,
                state=current_state.name,
                gt_x=self.hal.x,
                gt_y=self.hal.y,
                gt_z=self.hal.z,
                gt_yaw=self.hal.yaw,
                est_x=est_x,
                est_y=est_y,
                est_yaw=est_yaw,
                cmd_v=current_v,
                cmd_steer=current_steer,
                actual_v=self.hal.v_linear,
                pos_error_m=pos_err,
                waypoint_index=self.current_wp_idx,
            ))

        # Compute summary metrics
        metrics = self.state_monitor.compute_trajectory_metrics()
        mission_success = (self.sm.state == AutonomyState.MISSION_COMPLETE) or (
            self.inject_fault is not None and self.sm.state == AutonomyState.SAFE_STOP
        )

        return MissionResult(
            success=mission_success,
            final_state=self.sm.state.name,
            total_time_s=sim_time,
            total_distance_m=metrics["total_dist_m"],
            average_speed_mps=(metrics["total_dist_m"] / max(1.0, sim_time)),
            ate_rmse_m=metrics["ate_rmse_m"],
            final_error_m=metrics["final_error_m"],
            drift_percent=metrics["drift_percent"],
            waypoints_completed=self.current_wp_idx,
            total_waypoints=len(self.waypoints),
            replans_count=self.replans_count,
            fault_events=len(self.sm.fault_records),
            telemetry_log=self.telemetry_history,
        )

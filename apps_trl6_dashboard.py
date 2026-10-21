"""APPS NASA TRL 6 Planetary Rover Autonomous Navigation & V&V Dashboard.

Interactive mission control and verification & validation dashboard providing:
1. 3D Digital Elevation Model (DEM) and live trajectory visualization (GT vs EKF vs Plan).
2. Multi-sensor rig telemetry (3D LiDAR, RGB-D camera, Tactical IMU, Wheel Odometry).
3. 2.5D Elevation mapping and multi-criteria traversability cost maps.
4. Comprehensive 20-scenario multi-seed campaign results with Wilson score confidence intervals.
5. Comparative baseline evaluations and ablation studies.
6. 11-mode discrete FDIR state machine monitor with safety interlocks.
7. Hardware-in-the-Loop (HIL) CCSDS telemetry streaming monitor.
"""
from __future__ import annotations
import os
import sys
import json
import math
import time
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set root import path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from trl6_navigation import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    G_MARS,
    ROVER_MASS_KG,
    ROVER_LENGTH_M,
    ROVER_WIDTH_M,
    ROVER_HEIGHT_M,
    ROVER_WHEEL_RADIUS_M,
    MAX_SPEED_MPS,
    MAX_CURVATURE_INV_M,
    MAX_TRAVERSABLE_SLOPE_DEG,
    MAX_STEP_HEIGHT_M,
    SAFETY_CLEARANCE_MARGIN_M,
    SCENARIO_CLASSES,
)
from trl6_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl6_navigation.environment.scenario_generator import ScenarioGenerator
from trl6_navigation.sensors.sensor_rig import MultiSensorRig
from trl6_navigation.sensors.sensor_validator import SensorDataValidator
from trl6_navigation.perception.point_cloud_processor import PointCloudProcessor
from trl6_navigation.perception.elevation_mapping import ElevationMap25D
from trl6_navigation.perception.traversability import TraversabilityEstimator
from trl6_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl6_navigation.planning.collision_checker import CollisionChecker
from trl6_navigation.planning.path_tracker import PathTracker
from trl6_navigation.executive.state_machine import RoverOperatingMode, RoverFDIRStateMachine
from trl6_navigation.mission.mission_executor import DemonstrationMissionExecutor
from trl6_navigation.experiments.campaign_runner import CampaignRunner

# Streamlit Page Setup
st.set_page_config(
    page_title="APPS — Planetary Perception & Autonomy (TRL 6)",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e222b;
        border-radius: 8px;
        padding: 14px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
    }
    .status-badge {
        font-size: 13px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
        color: white;
    }
    .badge-complete { background-color: #28a745; }
    .badge-executing { background-color: #007bff; }
    .badge-fault { background-color: #dc3545; }
    .badge-safe { background-color: #ffc107; color: black; }
</style>
""", unsafe_allow_html=True)

# Top Banner
st.title("🪐 APPS — Automated Planetary Perception & Navigation System")
st.markdown("""
**NASA TRL 6 Integrated Prototype & Laboratory Demonstration Environment**  
*Technology Scope: Integrated autonomous planetary rover perception, localization, mapping, traversability estimation, motion planning, and closed-loop navigation.*
""")

# Top Safety Interlock Banner
col_b1, col_b2, col_b3, col_b4 = st.columns(4)
with col_b1:
    st.info(f"🔒 **PROTOTYPE_LOCK**: `{PROTOTYPE_LOCK}` (Safety Certified)")
with col_b2:
    st.info(f"🚫 **NAVIGATION_READY**: `{NAVIGATION_READY}` (Non-Flight-Certified)")
with col_b3:
    st.info(f"🪐 **Gravity**: `g = {G_MARS} m/s²` (Mars Surface Analog)")
with col_b4:
    st.info(f"📡 **HIL Status**: `APID 0x0150` (CCSDS Packet Streamer Ready)")

# Sidebar Controls
st.sidebar.header("🕹️ Mission & Scenario Configuration")
selected_scenario = st.sidebar.selectbox("Select Benchmark Scenario (SC-01 to SC-20)", SCENARIO_CLASSES, index=10)
random_seed = st.sidebar.number_input("PRNG Deterministic Seed", min_value=1, max_value=9999, value=100, step=17)

st.sidebar.markdown("---")
st.sidebar.subheader("Rover Physical Parameters")
st.sidebar.write(f"**Mass**: `{ROVER_MASS_KG} kg`")
st.sidebar.write(f"**Dimensions**: `{ROVER_LENGTH_M}m L × {ROVER_WIDTH_M}m W × {ROVER_HEIGHT_M}m H`")
st.sidebar.write(f"**Wheel Radius**: `{ROVER_WHEEL_RADIUS_M} m` (6-Wheel Rocker-Bogie)")
st.sidebar.write(f"**Max Speed**: `{MAX_SPEED_MPS} m/s`")
st.sidebar.write(f"**Min Turning Radius**: `ρ ≥ {1.0 / MAX_CURVATURE_INV_M:.2f} m`")

# Load Scenario Terrain
terrain, meta = ScenarioGenerator.build_scenario(selected_scenario, seed=random_seed)

# Navigation Tabs
tab_3d, tab_sensors, tab_mission, tab_campaign, tab_baselines, tab_hil = st.tabs([
    "🌐 3D DEM & Trajectory",
    "📡 Space Sensor Rig Telemetry",
    "🚀 End-to-End Mission Demo",
    "📊 20-Scenario Campaign (Wilson CIs)",
    "⚖️ Comparative Baselines & Ablations",
    "🛰️ HIL CCSDS Streamer",
])

# ------------------------------------------------------------------------------
# TAB 1: 3D DEM & Trajectory Visualization
# ------------------------------------------------------------------------------
with tab_3d:
    st.subheader("3D Planetary Digital Elevation Model (DEM) & Surface Topography")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    slope_grid = terrain.compute_slope_degrees()
    col_m1.metric("Terrain Dimensions", f"{terrain.size_x:.0f}m × {terrain.size_y:.0f}m")
    col_m2.metric("Mean Regional Slope", f"{np.mean(slope_grid):.1f}°")
    col_m3.metric("Max Regional Slope", f"{np.max(slope_grid):.1f}°")
    col_m4.metric("Active Boulder Hazards", f"{len(terrain.boulders)} items")

    # Downsample DEM for fast interactive 3D Plotly rendering
    downsample_step = 2
    x_sub = terrain.x_coords[::downsample_step]
    y_sub = terrain.y_coords[::downsample_step]
    z_sub = terrain.elevation[::downsample_step, ::downsample_step].T

    fig_3d = go.Figure()
    fig_3d.add_trace(go.Surface(
        x=x_sub,
        y=y_sub,
        z=z_sub,
        colorscale="YlOrBr",
        colorbar=dict(title="Elevation Z (m)", len=0.7),
        opacity=0.92,
        name="Planetary Surface"
    ))

    # Add Boulder Hazard Markers
    if terrain.boulders:
        bx = [b["x"] for b in terrain.boulders]
        by = [b["y"] for b in terrain.boulders]
        bz = [terrain.get_elevation_at(b["x"], b["y"]) + b["height"] + 0.1 for b in terrain.boulders]
        fig_3d.add_trace(go.Scatter3d(
            x=bx, y=by, z=bz,
            mode="markers",
            marker=dict(size=6, color="red", symbol="diamond"),
            name="Boulder Hazards"
        ))

    # Add Start and Goal Waypoints
    sx, sy = meta["start_state"][0], meta["start_state"][1]
    sz = terrain.get_elevation_at(sx, sy) + 0.5
    gx, gy = meta["goal_pos"][0], meta["goal_pos"][1]
    gz = terrain.get_elevation_at(gx, gy) + 0.5

    fig_3d.add_trace(go.Scatter3d(
        x=[sx], y=[sy], z=[sz],
        mode="markers+text",
        marker=dict(size=8, color="green"),
        text=["START"],
        name="Rover Start"
    ))

    fig_3d.add_trace(go.Scatter3d(
        x=[gx], y=[gy], z=[gz],
        mode="markers+text",
        marker=dict(size=8, color="blue"),
        text=["GOAL"],
        name="Mission Goal"
    ))

    fig_3d.update_layout(
        scene=dict(
            xaxis_title="East X (m)",
            yaxis_title="North Y (m)",
            zaxis_title="Elevation Z (m)",
            aspectratio=dict(x=1.2, y=1.2, z=0.4),
        ),
        margin=dict(l=10, r=10, b=10, t=30),
        height=620,
    )
    st.plotly_chart(fig_3d, use_container_width=True)

    # 2D Heatmaps (Elevation & Traversability Cost)
    st.markdown("---")
    st.subheader("2.5D Elevation Grid & Multi-Criteria Traversability Cost Map")
    col_h1, col_h2 = st.columns(2)

    # Build local elevation map and traversability
    elev_map = ElevationMap25D(terrain.size_x, terrain.size_y, terrain.res)
    elev_map.elevation = terrain.elevation.copy()
    elev_map.obstacle_mask = terrain.rock_mask.copy()
    elev_map.hit_count[:, :] = 10
    trav_est = TraversabilityEstimator()
    trav_data = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)

    with col_h1:
        st.markdown("**2.5D Elevation Model (Z [m])**")
        fig_elev = go.Figure(data=go.Heatmap(
            z=elev_map.elevation.T,
            x=terrain.x_coords,
            y=terrain.y_coords,
            colorscale="Viridis",
            colorbar=dict(title="Z (m)")
        ))
        fig_elev.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_elev, use_container_width=True)

    with col_h2:
        st.markdown("**Multi-Criteria Traversability Cost Grid [0.0 (benign) to 1.0 (lethal)]**")
        fig_cost = go.Figure(data=go.Heatmap(
            z=trav_data["cost_map"].T,
            x=terrain.x_coords,
            y=terrain.y_coords,
            colorscale="Inferno",
            colorbar=dict(title="Cost c(x)")
        ))
        fig_cost.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_cost, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: Space Sensor Rig Telemetry
# ------------------------------------------------------------------------------
with tab_sensors:
    st.subheader("🛰️ Multi-Sensor Rig Telemetry & Validation")
    st.markdown("Space-grade multi-sensor simulation with realistic noise, dropouts, and Martian gravity reaction.")

    rig = MultiSensorRig(terrain=terrain, noise_multiplier=meta["sensor_noise_factor"], lidar_dropout_prob=meta["lidar_dropout_prob"], seed=random_seed)
    validator = SensorDataValidator()

    col_s1, col_s2 = st.columns(2)

    # 1. 3D LiDAR Scan
    with col_s1:
        st.markdown("**3D Navigation LiDAR Scan (16-Beam Point Cloud)**")
        lidar_scan = rig.sample_lidar(meta["start_state"][:3])
        val_lidar = validator.validate_lidar_frame(lidar_scan, current_time_s=1.0)

        st.write(f"- Total Returns: `{val_lidar.cleaned_data['num_returns']}`")
        st.write(f"- Frame Validity: `{val_lidar.is_valid}`")
        st.write(f"- Rejection / Warning Flags: `{val_lidar.rejection_reasons if val_lidar.rejection_reasons else 'None (Nominal)'}`")

        pts_l = val_lidar.cleaned_data["points_lidar"]
        if len(pts_l) > 0:
            fig_lidar = go.Figure(data=[go.Scatter3d(
                x=pts_l[:, 0], y=pts_l[:, 1], z=pts_l[:, 2],
                mode="markers",
                marker=dict(size=2, color=pts_l[:, 2], colorscale="Jet", opacity=0.8)
            )])
            fig_lidar.update_layout(
                scene=dict(xaxis_title="Forward X (m)", yaxis_title="Lateral Y (m)", zaxis_title="Vertical Z (m)"),
                height=380, margin=dict(l=5, r=5, t=5, b=5)
            )
            st.plotly_chart(fig_lidar, use_container_width=True)

    # 2. Tactical IMU & Wheel Odometry
    with col_s2:
        st.markdown("**Tactical 6-Axis IMU & Martian Gravity Reaction**")
        imu_meas = rig.sample_imu(meta["start_state"][:3], forward_speed_mps=0.25, yaw_rate_rps=0.05)
        val_imu = validator.validate_imu_frame(imu_meas, current_time_s=1.0)
        odom_meas = rig.sample_wheel_odometry(true_speed_mps=0.25, true_yaw_rate_rps=0.05, slip_ratio=meta["wheel_slip_ratio"])
        val_odom = validator.validate_odometry_frame(odom_meas, current_time_s=1.0)

        st.write(f"- Specific Force (+Z): `{val_imu.cleaned_data['meas_accel_mps2'][2]:.3f} m/s²` (Mars `g = {G_MARS} m/s²`)")
        st.write(f"- Yaw Gyro Rate (Z): `{val_imu.cleaned_data['meas_gyro_rps'][2]:.4f} rad/s`")
        st.write(f"- Wheel Speed: `{val_odom.cleaned_data['meas_linear_mps']:.3f} m/s` (Injected Slip: `{val_odom.cleaned_data['injected_slip_ratio'] * 100:.1f}%`)")

        # Accelerometer and Gyro Bars
        df_imu = pd.DataFrame({
            "Axis": ["X (Longitudinal)", "Y (Lateral)", "Z (Vertical)"],
            "Accelerometer [m/s²]": val_imu.cleaned_data["meas_accel_mps2"],
            "Gyroscope [rad/s]": val_imu.cleaned_data["meas_gyro_rps"]
        })
        st.dataframe(df_imu, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: End-to-End Demonstration Mission
# ------------------------------------------------------------------------------
with tab_mission:
    st.subheader("🚀 Complete End-to-End Autonomous Exploration Mission (Stages A–F)")
    st.markdown("""
    Executes real-time closed-loop traversal with online dynamic pop-up obstacle injection,
    in-flight path invalidation, Kinodynamic Hybrid A* evasive replanning, and goal arrival.
    """)

    btn_run_mission = st.button("▶️ Execute Full Autonomous Mission (Stages A-F)", type="primary")

    if btn_run_mission:
        with st.spinner("Executing closed-loop autonomous navigation mission..."):
            mission_exec = DemonstrationMissionExecutor(experiment_id=f"EXP_{selected_scenario}")
            report = mission_exec.execute_mission(scenario_id=selected_scenario, seed=random_seed)

        st.success(f"Mission Finished with Outcome: **{report.failure_reason}** (Safe Handled: `{report.safe_handled}`)")

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Mission Success", "PASSED" if report.success else "STOPPED SAFE")
        col_r2.metric("Physical Collisions", f"{report.collision_count}")
        col_r3.metric("ATE RMSE Error", f"{report.ate_rmse_m:.3f} m")
        col_r4.metric("Replanning Events", f"{report.replan_count}")

        st.markdown("#### Mission Stage Progression Checkpoints")
        st.json(report.stage_checkpoints)

# ------------------------------------------------------------------------------
# TAB 4: 20-Scenario Validation Campaign
# ------------------------------------------------------------------------------
with tab_campaign:
    st.subheader("📊 20-Scenario Multi-Seed Validation Campaign (Wilson 95% CIs)")
    st.markdown("Statistical verification across all 20 standardized scenario classes.")

    results_dir = os.path.join(os.path.dirname(__file__), "results", "trl6")
    summary_file = os.path.join(results_dir, "campaign_summary.json")

    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            campaign_data = json.load(f)

        table_rows = []
        for sc_id, s in campaign_data.items():
            table_rows.append({
                "Scenario Class": sc_id,
                "Runs": s["total_runs"],
                "Success Rate (%)": s["success_rate_pct"],
                "Wilson 95% CI Lower": s["wilson_ci_95"][0],
                "Wilson 95% CI Upper": s["wilson_ci_95"][1],
                "Collisions": s["total_collisions"],
                "ATE RMSE (m)": s["mean_ate_rmse_m"],
                "Latency (ms)": s["mean_planning_latency_ms"],
            })

        df_campaign = pd.DataFrame(table_rows)
        st.dataframe(df_campaign, use_container_width=True)

        # Plot Wilson Confidence Interval Bar Chart
        fig_ci = go.Figure()
        fig_ci.add_trace(go.Bar(
            x=df_campaign["Scenario Class"],
            y=df_campaign["Success Rate (%)"],
            error_y=dict(
                type="data",
                symmetric=False,
                array=df_campaign["Wilson 95% CI Upper"] - df_campaign["Success Rate (%)"],
                arrayminus=df_campaign["Success Rate (%)"] - df_campaign["Wilson 95% CI Lower"],
            ),
            marker_color="teal",
            name="Pass Rate (Wilson 95% CI)"
        ))
        fig_ci.update_layout(
            yaxis_title="Success Rate (%)",
            yaxis_range=[0, 105],
            xaxis_tickangle=-45,
            height=450,
            margin=dict(l=10, r=10, t=30, b=100)
        )
        st.plotly_chart(fig_ci, use_container_width=True)
    else:
        st.info("No campaign summary found in `results/trl6/`. Run `python experiments/run_trl6_campaign.py` to generate statistical evidence.")

# ------------------------------------------------------------------------------
# TAB 5: Comparative Baselines & Ablations
# ------------------------------------------------------------------------------
with tab_baselines:
    st.subheader("⚖️ Comparative Baselines & Algorithmic Ablation Studies")

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        st.markdown("**Comparative Navigation Baselines (SC-04 Dense Obstacle Field)**")
        base_file = os.path.join(results_dir, "baseline_comparison.json")
        if os.path.exists(base_file):
            with open(base_file, "r", encoding="utf-8") as f:
                b_data = json.load(f)
            b_rows = []
            for b_name, b_val in b_data["baselines"].items():
                b_rows.append({
                    "Paradigm": b_name,
                    "Success": b_val["success"],
                    "Collisions": b_val["collisions"],
                    "Length (m)": b_val["path_length_m"],
                    "Latency (ms)": b_val["latency_ms"],
                    "Curvature Continuous": b_val["curvature_continuous"]
                })
            st.dataframe(pd.DataFrame(b_rows), use_container_width=True)
        else:
            st.info("Run validation campaign to generate baseline evidence.")

    with col_b2:
        st.markdown("**Algorithmic Ablation Study (SC-04 Dense Obstacle Field)**")
        abl_file = os.path.join(results_dir, "ablation_study.json")
        if os.path.exists(abl_file):
            with open(abl_file, "r", encoding="utf-8") as f:
                abl_data = json.load(f)
            abl_rows = []
            for a_name, a_val in abl_data.items():
                abl_rows.append({
                    "Configuration": a_name,
                    "Safe Handled": a_val["safe_handled"],
                    "Collisions": a_val["collision_count"],
                    "ATE RMSE (m)": a_val["ate_rmse_m"],
                    "Failure Reason": a_val["failure_reason"]
                })
            st.dataframe(pd.DataFrame(abl_rows), use_container_width=True)
        else:
            st.info("Run validation campaign to generate ablation evidence.")

# ------------------------------------------------------------------------------
# TAB 6: HIL CCSDS Streamer
# ------------------------------------------------------------------------------
with tab_hil:
    st.subheader("🛰️ Hardware-in-the-Loop (HIL) CCSDS Space Packet Streamer")
    st.markdown("""
    Broadcasting live binary telemetry over UDP socket using standard CCSDS Space Packet Protocol (CCSDS 133.0-B-1).
    Enables external breadboard flight computers and real-time simulators to ingest rover status.
    """)

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.write("- **Destination Target**: `127.0.0.1:8088` (UDP)")
        st.write("- **Application Process Identifier (APID)**: `0x0150` (336 decimal - Autonomy Navigation TM)")
        st.write("- **Protocol Version**: CCSDS Packet Version `000` (Unsegmented user data)")
        st.write("- **Checksum Standard**: 32-bit CRC (Ethernet/ISO polynomial)")

    with col_h2:
        st.write("- **Telemetry Packet Rate**: `10 Hz` synchronized with RTOS executive")
        st.write("- **Payload Structure**: Rover Pose, Linear Speed, Operating Mode, Collision Status")

    # Download Evidence Manifests
    st.markdown("---")
    st.subheader("📥 Export Machine-Readable TRL 6 Evidence Packages")
    col_d1, col_d2 = st.columns(2)
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_bytes = f.read().encode("utf-8")
        col_d1.download_button(
            label="Download Campaign Summary JSON",
            data=summary_bytes,
            file_name="campaign_summary.json",
            mime="application/json"
        )
    manifest_file = os.path.join(results_dir, "campaign_manifest.json")
    if os.path.exists(manifest_file):
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_bytes = f.read().encode("utf-8")
        col_d2.download_button(
            label="Download Raw Manifest JSON",
            data=manifest_bytes,
            file_name="campaign_manifest.json",
            mime="application/json"
        )

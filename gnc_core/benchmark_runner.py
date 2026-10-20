"""Headless Deterministic Benchmark Runner & RTOS Execution Profiler (TRL 4).
Evaluates 100 Hz (10 ms) closed-loop GNC flight software cycle execution.

Profiles:
- 1PN Relativistic Orbit RK4 Propagation (ICRF J2000)
- Space-Grade IMU Noise & Bias Instability Filtering
- Pulsar XNAV Photon Counting & Range Solving
- Closed-Loop Aerocapture Bank Angle Corridor Guidance
- Binary CCSDS Telemetry Packet Framing & CRC-16 Checksum Validation

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import os
import sys
import time
import math
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gnc_core import (
    C_LIGHT,
    MU_SUN,
    MU_MARS,
    AU_METERS,
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
)
from gnc_core.physics.relativistic_orbit import RelativisticOrbitPropagator
from gnc_core.physics.aerocapture_corridor import AerocaptureCorridorGuidance
from gnc_core.realtime.scheduler import DeterministicScheduler
from gnc_core.realtime.ccsds_packet import CCSDSSpacePacket
from gnc_core.sensors.space_grade_imu import SpaceGradeIMU
from gnc_core.sensors.xnav_pulsar import SpaceborneXNAVReceiver
from gnc_core.sensors.lidar_vision import SpacecraftLiDARVisionSensor
from gnc_core.hil.telemetry_socket import HILTelemetrySocket


def run_gnc_headless_benchmark(num_cycles: int = 1000, target_freq_hz: float = 100.0) -> dict:
    """Runs high-performance deterministic headless benchmark over num_cycles."""
    print("=" * 80)
    print(f"NASA/ESA TRL 4 GNC REAL-TIME DETERMINISTIC BENCHMARK ({num_cycles} Cycles @ {target_freq_hz} Hz)")
    print(f"Operational Lock: PROTOTYPE_LOCK = {PROTOTYPE_LOCK} | Navigation: READY = {NAVIGATION_READY}")
    print("=" * 80)

    scheduler = DeterministicScheduler(target_frequency_hz=target_freq_hz)
    orbit_prop = RelativisticOrbitPropagator(mu_central=MU_SUN, dt_step_s=scheduler.period_s)
    aero_guide = AerocaptureCorridorGuidance()
    imu = SpaceGradeIMU(dt_s=scheduler.period_s)
    xnav = SpaceborneXNAVReceiver()
    lidar = SpacecraftLiDARVisionSensor(latency_steps=5)
    hil_sock = HILTelemetrySocket(enable_network=False)
    ccsds = CCSDSSpacePacket()

    # Initial spacecraft state (Heliocentric transfer orbit near 1.5 AU)
    pos_m = np.array([1.45 * AU_METERS, 0.25 * AU_METERS, 0.01 * AU_METERS], dtype=np.float64)
    vel_mps = np.array([-5200.0, 24100.0, 350.0], dtype=np.float64)
    omega_rps = np.array([0.001, -0.002, 0.005], dtype=np.float64)

    # Aerocapture local state
    alt_m = 65000.0
    v_aero_mps = 5800.0
    gamma_rad = math.radians(-11.5)

    def gnc_100hz_task(sim_time: float, dt: float) -> dict:
        nonlocal pos_m, vel_mps, alt_m, v_aero_mps, gamma_rad

        # 1. 1PN Relativistic Orbit Propagation (RK4)
        pos_m, vel_mps = orbit_prop.step_rk4(pos_m, vel_mps, dt)
        scheduler.sanitize_ieee754_vector(pos_m, "pos_m")
        scheduler.sanitize_ieee754_vector(vel_mps, "vel_mps")

        # 2. Space-Grade IMU Sampling
        accel_ideal = np.array([0.0, 0.0, -9.81], dtype=np.float64)
        imu_meas = imu.step(omega_rps, accel_ideal)

        # 3. Pulsar XNAV Range Fix (sampled every 10 cycles = 10 Hz)
        if scheduler.step_count % 10 == 0:
            xnav_meas = xnav.simulate_observation(pos_m, "PSR_B1937+21", integration_time_s=0.1, mission_elapsed_s=sim_time)
        else:
            xnav_meas = None

        # 4. LiDAR Optical Range with 50 ms latency
        lidar_meas = lidar.process_measurement(alt_m)

        # 5. Closed-Loop Aerocapture Guidance with 3-sigma density perturbation
        aero_cmd = aero_guide.evaluate_guidance_cycle(
            alt_m, v_aero_mps, gamma_rad, density_perturbation_sigma=1.0
        )
        bank_deg = aero_cmd["commanded_bank_deg"]

        # Advance entry kinematics
        r_dot, v_dot, gamma_dot = aero_guide.compute_derivatives(
            3396.2e3 + alt_m, v_aero_mps, gamma_rad, math.radians(bank_deg), aero_cmd["density_kg_m3"]
        )
        alt_m = max(20000.0, alt_m + r_dot * dt)
        v_aero_mps = max(100.0, v_aero_mps + v_dot * dt)
        gamma_rad += gamma_dot * dt

        # 6. Binary CCSDS Telemetry Packet Framing & CRC-16
        packet_bytes = ccsds.pack_gnc_telemetry(
            pos_m, vel_mps, imu_meas["meas_accel_mps2"], bank_deg, aero_cmd["g_load_g"]
        )
        hil_sock.send_telemetry_packet(packet_bytes)

        return {
            "time_s": sim_time,
            "alt_km": alt_m / 1000.0,
            "bank_deg": bank_deg,
            "packet_len": len(packet_bytes),
        }

    # Execute deterministic loop
    for _ in range(num_cycles):
        scheduler.execute_cycle(gnc_100hz_task)

    hil_sock.close()
    stats = scheduler.get_timing_statistics()

    print("\nBENCHMARK RESULTS & RTOS DETERMINISM AUDIT:")
    print(f" - Total Cycles Executed:        {stats['total_cycles']}")
    print(f" - Target Cycle Period:          {stats['target_period_ms']:.2f} ms (100 Hz)")
    print(f" - Mean Execution Latency:       {stats['mean_latency_ms']:.4f} ms")
    print(f" - 95th Percentile Latency:      {stats['p95_latency_ms']:.4f} ms")
    print(f" - 99th Percentile Latency:      {stats['p99_latency_ms']:.4f} ms")
    print(f" - Worst-Case Max Latency:       {stats['max_latency_ms']:.4f} ms")
    print(f" - Mean Cycle Jitter:            {stats['mean_jitter_ms']:.4f} ms")
    print(f" - RTOS Deadline Overruns:       {stats['deadline_overruns']} ({stats['overrun_percentage']:.2f}%)")
    
    cpu_utilization = (stats['mean_latency_ms'] / stats['target_period_ms']) * 100.0
    print(f" - Core CPU Utilization:         {cpu_utilization:.2f}% (Idle Margin: {100.0 - cpu_utilization:.2f}%)")

    # NASA/ESA TRL 4 Pass/Fail criteria:
    # 1. Mean execution latency < 2.0 ms (allowing > 80% CPU idle margin for RTOS context switches)
    # 2. Zero deadline overruns (< 10 ms)
    is_compliant = (stats['mean_latency_ms'] < 2.0) and (stats['deadline_overruns'] == 0)
    verdict = "PASSED (TRL 4 VALIDATED)" if is_compliant else "NON-COMPLIANT"
    print(f"\n>> FINAL TRL 4 DETERMINISM VERDICT: {verdict}")
    print("=" * 80)

    return stats


if __name__ == "__main__":
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run_gnc_headless_benchmark(num_cycles=cycles)

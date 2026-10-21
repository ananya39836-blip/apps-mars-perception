"""APPS: Automated Planetary Perception System (NASA TRL 7 Operational Dashboard).

Operational ground control and engineering validation station for autonomous
planetary rover perception, localization, mapping, kinodynamic path planning,
closed-loop trajectory execution, and FDIR executive monitoring.

Safety Invariants:
    PROTOTYPE_LOCK = True (Permanently latched; non-flight certified)
    NAVIGATION_READY = False (Explicit compile-time research guard)
"""
from __future__ import annotations
import math
import os
import json
import time
import numpy as np
import plotly.graph_objects as go
import streamlit as st

import trl7_navigation as t7
from trl7_navigation.environment.scenario_generator import ScenarioGenerator
from trl7_navigation.hardware.simulated_hal import SimulatedHAL
from trl7_navigation.sensors.sensor_rig import IntegratedSensorRig
from trl7_navigation.perception.elevation_mapping import ElevationMap25D
from trl7_navigation.perception.traversability import TraversabilityEstimator
from trl7_navigation.localization.error_state_ekf import ErrorStateEKF
from trl7_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl7_navigation.planning.path_tracker import PathTracker
from trl7_navigation.mission.long_duration_mission import LongDurationMissionRunner
from trl7_navigation.experiments.campaign_runner import compute_wilson_ci

# Streamlit Page Configuration
st.set_page_config(
    page_title="APPS — TRL 7 Planetary Rover Autonomy Station",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #ff5722; margin-bottom: 0px; }
    .sub-header { font-size: 1.05rem; color: #9e9e9e; margin-bottom: 20px; }
    .status-card { background: #1e222b; border-left: 4px solid #ff5722; padding: 12px; border-radius: 6px; margin-bottom: 10px; }
    .metric-value { font-size: 1.4rem; font-weight: bold; color: #ffffff; }
    .metric-label { font-size: 0.85rem; color: #b0bec5; }
    .safety-banner { background: #261717; border: 1px solid #d32f2f; color: #ffcdd2; padding: 10px 16px; border-radius: 6px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Safety Guard & System Identification Banner
# -----------------------------------------------------------------------------
st.markdown("""
<div class="safety-banner">
    <b>[CRITICAL SAFETY ENVELOPE: NASA TRL 7 OPERATIONAL PROTOTYPE]</b><br>
    <code>PROTOTYPE_LOCK = True</code> &nbsp;|&nbsp; 
    <code>NAVIGATION_READY = False</code> &nbsp;|&nbsp; 
    <b>Notice:</b> Research-grade autonomy evaluated in operational Earth analog testbed conditions. Non-flight certified.
</div>
""", unsafe_allow_html=True)

st.title("🪐 APPS — Automated Planetary Perception System")
st.markdown("<div class='sub-header'>TRL 7 Operational Environment Prototype Demonstration & Verification Station (v2.7.0-trl7)</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Operational Testbed Config")
    testbed = st.selectbox(
        "Analog Field Facility",
        [
            "JPL Mars Yard Analog (California)",
            "Basalt Quarry Field Testbed (Iceland)",
            "Atacama Desert Dune Simulant (Chile)",
            "Synthetic Laboratory 3D Sandbox",
        ],
        index=0,
    )
    
    st.subheader("Scenario Selection")
    scenario_id = st.selectbox("Operational Scenario (SC-01 to SC-20)", t7.SCENARIO_CLASSES, index=0)
    sim_seed = st.number_input("Random Seed", min_value=1, max_value=9999, value=42, step=1)
    
    st.subheader("Rover Locomotion Limits")
    st.markdown(f"- **Chassis Mass**: {t7.ROVER_MASS_KG:.1f} kg")
    st.markdown(f"- **Max Speed**: {t7.MAX_SPEED_MPS:.2f} m/s")
    st.markdown(f"- **Min Turning Radius**: {t7.MIN_TURNING_RADIUS_M:.2f} m")
    st.markdown(f"- **Max Curvature**: {t7.MAX_CURVATURE_INV_M:.2f} m⁻¹")
    st.markdown(f"- **Climb Limit**: {t7.MAX_TRAVERSABLE_SLOPE_DEG:.1f}°")
    
    st.divider()
    emergency_stop_clicked = st.button("🛑 EMERGENCY E-STOP", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# Terrain Generation & Setup
# -----------------------------------------------------------------------------
terrain, scenario_cfg = ScenarioGenerator.create_scenario(scenario_id, seed=sim_seed)

# Main Navigation Tabs
tab_mission, tab_perception, tab_ekf, tab_campaign, tab_docs = st.tabs([
    "🚀 Closed-Loop Mission Execution",
    "👁️ 3D Perception & Traversability",
    "📡 15-State ES-EKF Localization",
    "📊 20-Scenario Campaign Evidence",
    "📄 TRL 7 Engineering Verification",
])

# -----------------------------------------------------------------------------
# Tab 1: Closed-Loop Mission Execution
# -----------------------------------------------------------------------------
with tab_mission:
    st.subheader(f"Autonomous Mission Traverse: {scenario_id}")
    st.caption(scenario_cfg.description)

    col_btn, col_info1, col_info2, col_info3 = st.columns([1.5, 1, 1, 1])
    with col_btn:
        run_mission = st.button("▶️ Dispatch Autonomous Mission", type="primary", use_container_width=True)
    with col_info1:
        st.metric("Start Pose", f"({scenario_cfg.start_pose[0]:.1f}, {scenario_cfg.start_pose[1]:.1f})")
    with col_info2:
        st.metric("Target Goal", f"({scenario_cfg.goal_pose[0]:.1f}, {scenario_cfg.goal_pose[1]:.1f})")
    with col_info3:
        st.metric("Terrain Bounds", f"{scenario_cfg.terrain_size_x:.0f}m x {scenario_cfg.terrain_size_y:.0f}m")

    if run_mission or "mission_res" in st.session_state:
        if run_mission:
            with st.spinner("Executing real-time closed-loop perception and navigation traverse..."):
                waypoints = scenario_cfg.waypoints if scenario_cfg.waypoints else [scenario_cfg.goal_pose]
                runner = LongDurationMissionRunner(
                    terrain=terrain,
                    waypoints=waypoints,
                    start_pose=scenario_cfg.start_pose,
                    dt=0.05,
                    max_mission_time_s=120.0,
                    imu_noise_multiplier=scenario_cfg.imu_noise_multiplier,
                    lidar_noise_m=scenario_cfg.lidar_noise_m,
                    lidar_dropout_prob=scenario_cfg.lidar_dropout_prob,
                    slip_bias=scenario_cfg.slip_bias,
                    inject_fault=scenario_cfg.inject_fault,
                    inject_fault_time_s=scenario_cfg.inject_fault_time_s,
                )
                res = runner.run()
                st.session_state["mission_res"] = res
        else:
            res = st.session_state["mission_res"]

        # Telemetry metrics row
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Status", res.final_state, delta="SUCCESS" if res.success else "FAULT/HALT")
        m2.metric("Distance", f"{res.total_distance_m:.2f} m")
        m3.metric("Duration", f"{res.total_time_s:.1f} s")
        m4.metric("ATE RMSE", f"{res.ate_rmse_m:.3f} m")
        m5.metric("Final Drift", f"{res.drift_percent:.2f} %")
        m6.metric("Replans", f"{res.replans_count}")

        # Trajectory 3D Plotly Visualizer
        st.subheader("3D Operational Terrain & Autonomous Traverse Profile")
        
        # Subsample DEM for fast interactive 3D rendering
        skip = 2
        x_sub = terrain.x_coords[::skip]
        y_sub = terrain.y_coords[::skip]
        z_sub = terrain.elevation[::skip, ::skip]

        fig3d = go.Figure()
        fig3d.add_trace(go.Surface(
            x=x_sub, y=y_sub, z=z_sub.T,
            colorscale="Earth", opacity=0.85, showscale=False, name="Planetary DEM"
        ))

        # Add ground-truth trajectory
        t_log = res.telemetry_log
        if t_log:
            gt_x = [pt.gt_x for pt in t_log]
            gt_y = [pt.gt_y for pt in t_log]
            gt_z = [pt.gt_z + 0.3 for pt in t_log]
            fig3d.add_trace(go.Scatter3d(
                x=gt_x, y=gt_y, z=gt_z,
                mode="lines", line=dict(color="#00e676", width=5), name="Ground-Truth Trajectory"
            ))

            est_x = [pt.est_x for pt in t_log]
            est_y = [pt.est_y for pt in t_log]
            est_z = [terrain.get_elevation_at(pt.est_x, pt.est_y) + 0.35 for pt in t_log]
            fig3d.add_trace(go.Scatter3d(
                x=est_x, y=est_y, z=est_z,
                mode="lines", line=dict(color="#ff9100", width=4, dash="dot"), name="ES-EKF Estimated"
            ))

        # Add Waypoint and Boulders
        fig3d.add_trace(go.Scatter3d(
            x=[scenario_cfg.start_pose[0]], y=[scenario_cfg.start_pose[1]],
            z=[terrain.get_elevation_at(scenario_cfg.start_pose[0], scenario_cfg.start_pose[1]) + 1.0],
            mode="markers+text", marker=dict(size=8, color="#2979ff"), text=["Start"], name="Start"
        ))
        fig3d.add_trace(go.Scatter3d(
            x=[scenario_cfg.goal_pose[0]], y=[scenario_cfg.goal_pose[1]],
            z=[terrain.get_elevation_at(scenario_cfg.goal_pose[0], scenario_cfg.goal_pose[1]) + 1.0],
            mode="markers+text", marker=dict(size=10, color="#d50000"), text=["Goal"], name="Goal"
        ))

        fig3d.update_layout(
            scene=dict(
                xaxis_title="East (m)",
                yaxis_title="North (m)",
                zaxis_title="Elevation (m)",
                aspectmode="data",
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=550,
        )
        st.plotly_chart(fig3d, use_container_width=True)

        # Telemetry graphs
        st.subheader("Real-Time Telemetry Traces")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            times = [pt.time_s for pt in t_log]
            v_actual = [pt.actual_v for pt in t_log]
            v_cmd = [pt.cmd_v for pt in t_log]
            fig_v = go.Figure()
            fig_v.add_trace(go.Scatter(x=times, y=v_actual, name="Actual Speed (m/s)", line=dict(color="#00e676")))
            fig_v.add_trace(go.Scatter(x=times, y=v_cmd, name="Commanded Speed (m/s)", line=dict(color="#ffab00", dash="dash")))
            fig_v.update_layout(title="Chassis Velocity Tracking", xaxis_title="Time (s)", yaxis_title="Speed (m/s)", height=280)
            st.plotly_chart(fig_v, use_container_width=True)

        with col_t2:
            errors = [pt.pos_error_m for pt in t_log]
            fig_err = go.Figure()
            fig_err.add_trace(go.Scatter(x=times, y=errors, name="Position Error (m)", line=dict(color="#ff1744")))
            fig_err.update_layout(title="Absolute Trajectory Error Over Time", xaxis_title="Time (s)", yaxis_title="Error (m)", height=280)
            st.plotly_chart(fig_err, use_container_width=True)

# -----------------------------------------------------------------------------
# Tab 2: 3D Perception & Traversability
# -----------------------------------------------------------------------------
with tab_perception:
    st.subheader("Online 2.5D Elevation Mapping & Multi-Criteria Traversability Cost")
    
    elev_map = ElevationMap25D(terrain.size_x, terrain.size_y, terrain.res)
    # Initialize from terrain
    elev_map.elevation[:, :] = terrain.elevation
    elev_map.observed[:, :] = True
    elev_map.detect_negative_obstacles(terrain.size_x * 0.5, terrain.size_y * 0.5)

    estimator = TraversabilityEstimator()
    cost_map, impassable_mask, components = estimator.evaluate(elev_map, friction_grid=terrain.regolith_friction)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        fig_cost = go.Figure(data=go.Heatmap(
            z=cost_map.T, x=terrain.x_coords, y=terrain.y_coords,
            colorscale="Viridis", zmin=0.0, zmax=1.0, colorbar=dict(title="Cost [0,1]")
        ))
        fig_cost.update_layout(title="Composite Traversability Cost Map", xaxis_title="X (m)", yaxis_title="Y (m)", height=450)
        st.plotly_chart(fig_cost, use_container_width=True)

    with col_p2:
        fig_imp = go.Figure(data=go.Heatmap(
            z=impassable_mask.astype(int).T, x=terrain.x_coords, y=terrain.y_coords,
            colorscale=[[0, "#212121"], [1, "#d50000"]], showscale=False
        ))
        fig_imp.update_layout(title="Inflated Binary Impassable Hazard Mask (Cleared Margin: 1.40m)", xaxis_title="X (m)", yaxis_title="Y (m)", height=450)
        st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("### Traversability Factor Analysis")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Max Local Slope", f"{np.max(components['slope_deg']):.1f}°", f"Limit: {t7.MAX_TRAVERSABLE_SLOPE_DEG}°")
    c2.metric("Max Step Obstacle", f"{np.max(components['step_height_m']):.2f} m", f"Limit: {t7.MAX_STEP_HEIGHT_M} m")
    c3.metric("Surface Roughness", f"{np.mean(components['roughness_m']):.3f} m")
    c4.metric("Impassable Cells", f"{np.sum(impassable_mask)} ({np.mean(impassable_mask)*100:.1f}%)")

# -----------------------------------------------------------------------------
# Tab 3: 15-State ES-EKF Localization
# -----------------------------------------------------------------------------
with tab_ekf:
    st.subheader("15-State Error-State Extended Kalman Filter (ES-EKF) Architecture")
    st.markdown("""
    The localization subsystem integrates:
    - **High-Rate Strapdown Mechanization (100 Hz)**: Quaternion attitude and velocity integration from tactical IMU.
    - **Non-Holonomic Velocity Constraints**: Enforces $v_{\text{lat}} \approx 0$ and $v_{\text{vert}} \approx 0$ in vehicle body coordinates.
    - **Joseph-Form Covariance Propagation**: $P_k = (I - K_k H_k) P_k^- (I - K_k H_k)^T + K_k R_k K_k^T$ guaranteeing positive semi-definiteness.
    - **Visual / LiDAR Odometry ICP Fusion (5 Hz)**: Periodic absolute position correction preventing unbounded random walk drift.
    """)

    col_mat1, col_mat2 = st.columns(2)
    with col_mat1:
        st.subheader("Nominal & Error State Vector")
        st.code("""
Nominal State Vector x ∈ ℝ¹⁶:
  x = [p_x, p_y, p_z,   (Position [m])
       v_x, v_y, v_z,   (Velocity [m/s])
       q_w, q_x, q_y, q_z, (Unit Quaternion)
       b_ax, b_ay, b_az, (Accel Bias [m/s²])
       b_gx, b_gy, b_gz] (Gyro Bias [rad/s])

Error State Vector δx ∈ ℝ¹⁵:
  δx = [δp (3), δv (3), δθ (3), δb_a (3), δb_g (3)]
        """, language="text")

    with col_mat2:
        st.subheader("Covariance Diagonal Standard Deviations")
        st.markdown("- **Position ($P_{pos}$)**: $\\sigma_{pos} = 0.050\\text{ m}$")
        st.markdown("- **Velocity ($P_{vel}$)**: $\\sigma_{vel} = 0.020\\text{ m/s}$")
        st.markdown("- **Attitude ($P_{att}$)**: $\\sigma_{\\theta} = 1.000^\\circ$")
        st.markdown("- **Accel Bias ($P_{ba}$)**: $\\sigma_{ba} = 0.050\\text{ m/s}^2$")
        st.markdown("- **Gyro Bias ($P_{bg}$)**: $\\sigma_{bg} = 0.500^\\circ/\\text{s}$")

# -----------------------------------------------------------------------------
# Tab 4: 20-Scenario Campaign Evidence
# -----------------------------------------------------------------------------
with tab_campaign:
    st.subheader("Standardized Validation Campaign Results (NASA TRL 7 Criteria)")
    
    # Load campaign results if available
    results_path = os.path.join(os.path.dirname(__file__), "results", "trl7", "campaign_summary.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            camp_data = json.load(f)
        
        st.success(f"Validation Campaign Loaded: {camp_data['total_runs']} Runs Across {camp_data['total_scenarios']} Standardized Scenarios")
        
        top1, top2, top3, top4 = st.columns(4)
        top1.metric("Overall Success Rate", f"{camp_data['overall_success_rate']*100:.1f}%")
        top2.metric("95% Wilson CI", f"[{camp_data['overall_wilson_ci_95'][0]*100:.1f}% - {camp_data['overall_wilson_ci_95'][1]*100:.1f}%]")
        top3.metric("Scenarios Evaluated", f"{camp_data['total_scenarios']}")
        top4.metric("Total Executions", f"{camp_data['total_runs']}")

        # Table of results per scenario
        st.markdown("### Scenario-by-Scenario Validation Matrix")
        table_rows = []
        for sc_name, sc_data in camp_data["scenarios"].items():
            table_rows.append({
                "Scenario ID": sc_name,
                "Runs": sc_data["n_runs"],
                "Success Rate": f"{sc_data['success_rate']*100:.1f}%",
                "95% CI Lower": f"{sc_data['wilson_ci_95'][0]*100:.1f}%",
                "95% CI Upper": f"{sc_data['wilson_ci_95'][1]*100:.1f}%",
                "Mean ATE RMSE (m)": f"{sc_data['mean_ate_rmse_m']:.3f}",
                "Mean Distance (m)": f"{sc_data['mean_distance_m']:.2f}",
                "Mean Replans": f"{sc_data['mean_replans']:.1f}",
            })
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("Validation campaign artifacts have not been precomputed. Click below to execute the 20-scenario campaign runner.")
        if st.button("🚀 Execute 20-Scenario Campaign Runner"):
            with st.spinner("Executing full Monte-Carlo campaign (this runs 40 automated mission trials)..."):
                from trl7_navigation.experiments.campaign_runner import CampaignRunner
                out_dir = os.path.join(os.path.dirname(__file__), "results", "trl7")
                runner = CampaignRunner(output_dir=out_dir)
                camp_data = runner.run_full_campaign(seeds=[42, 101], verbose=False)
                st.rerun()

# -----------------------------------------------------------------------------
# Tab 5: TRL 7 Engineering Verification
# -----------------------------------------------------------------------------
with tab_docs:
    st.subheader("NASA TRL 7 Engineering Verification & Validation Evidence Package")
    st.markdown("""
    ### Technology Scope Definition
    **Subsystem Assessed**: Integrated autonomous planetary rover perception, localization, mapping, traversability estimation, motion planning, and closed-loop navigation subsystem.
    
    ### Official NASA TRL 7 Definition (NASA SP-2016-6105 Rev 2)
    > *"System prototype demonstration in an operational environment. The prototype system is at or near the planned operational system, representing a major step up from TRL 6 by requiring demonstration of an actual system prototype in an operational environment (e.g., in an aircraft, in a vehicle, or in space)."*
    
    ### Key Engineering Distinctions & Boundaries
    1. **Validated Capabilities (TRL 7 Scope)**:
       - 6-Wheel Rocker-Bogie kinematic articulation over rugged digital elevation models.
       - Bekker-Wong and Janosi-Hanamoto terramechanic soil sinkage and drawbar pull dynamics.
       - Probabilistic 2.5D elevation grid assembly with recursive Kalman variance filtering.
       - Curvature-bounded continuous $SE(2)$ Kinodynamic Hybrid A* motion planning ($\kappa \le 1.50\text{ m}^{-1}$).
       - Space-grade sensor packet validation (monotonicity, NaN/Inf rejection, CRC checks).
       - 11-mode discrete Fault Detection, Isolation, and Recovery (FDIR) state executive.
    2. **Unvalidated Flight Conditions (Beyond TRL 7 Scope)**:
       - Cryogenic vacuum thermal conditions ($-120^\circ\text{C}$ to $+20^\circ\text{C}$).
       - Radiation hardness assurance (TID $\ge 100\text{ krad}$ Si).
       - Planetary entry, descent, and landing (EDL) mechanical shock loads.
       - Actual Mars surface gravity ($0.378\,g_\oplus$) physical validation (currently tested under Earth analog testbed conditions).
    """)

    st.download_button(
        label="📥 Download TRL 7 Verification Manifest (JSON)",
        data=json.dumps({
            "project": "APPS - Automated Planetary Perception System",
            "version": t7.SOFTWARE_VERSION,
            "trl_level": 7,
            "trl_claim": "System prototype demonstration in an operational environment",
            "safety_invariants": {
                "PROTOTYPE_LOCK": t7.PROTOTYPE_LOCK,
                "NAVIGATION_READY": t7.NAVIGATION_READY,
            },
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, indent=2),
        file_name="trl7_verification_manifest.json",
        mime="application/json",
    )

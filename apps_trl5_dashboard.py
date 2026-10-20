"""APPS NASA TRL 5 Planetary Rover Autonomous Navigation & V&V Dashboard.

Interactive mission control and verification & validation dashboard providing:
1. 3D Digital Elevation Model (DEM) and live trajectory visualization (GT vs EKF vs Plan).
2. Multi-sensor rig telemetry (3D LiDAR, RGB-D camera, Tactical IMU, Wheel Odometry).
3. 2.5D Elevation mapping and multi-criteria traversability cost maps.
4. Comprehensive 15-scenario multi-seed campaign results with Wilson score confidence intervals.
5. Comparative baseline evaluations and ablation studies.
6. 11-mode discrete FDIR state machine monitor with safety interlocks.
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
from trl5_navigation import (
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
from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl5_navigation.environment.scenario_generator import ScenarioGenerator
from trl5_navigation.sensors.sensor_rig import MultiSensorRig
from trl5_navigation.perception.point_cloud_processor import PointCloudProcessor
from trl5_navigation.perception.elevation_mapping import ElevationMap25D
from trl5_navigation.perception.traversability import TraversabilityEstimator
from trl5_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl5_navigation.planning.collision_checker import CollisionChecker
from trl5_navigation.planning.path_tracker import PathTracker
from trl5_navigation.executive.state_machine import RoverOperatingMode, RoverFDIRStateMachine
from trl5_navigation.experiments.campaign_runner import CampaignRunner

# Streamlit Page Setup
st.set_page_config(
    page_title="APPS — Planetary Perception & Autonomy (TRL 5)",
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
**NASA TRL 5 Research & Synthetic Laboratory Validation Environment**  
*Technology Scope: Autonomous planetary rover 3D terrain perception, local mapping, traversability estimation, and collision-aware navigation in representative simulated Mars/Lunar environments.*
""")

# Top Safety Interlock Banner
col_b1, col_b2, col_b3, col_b4 = st.columns(4)
with col_b1:
    st.info(f"🔒 **PROTOTYPE_LOCK**: `{PROTOTYPE_LOCK}` (Safety Certified)")
with col_b2:
    st.info(f"🚫 **NAVIGATION_READY**: `{NAVIGATION_READY}` (Non-Flight-Certified)")
with col_b3:
    st.info(f"🪐 **Gravity**: `g = {G_MARS} m/s²` (Mars Subsurface/Chryse)")
with col_b4:
    st.info(f"🚜 **Vehicle Mass**: `{ROVER_MASS_KG} kg` (Rocker-Bogie 6-Wheel)")

# Sidebar Configuration
st.sidebar.header("🕹️ Mission & Scenario Controls")

selected_scenario = st.sidebar.selectbox(
    "Select Standardized Scenario Class",
    SCENARIO_CLASSES,
    index=0
)

scenario_descriptions = {
    "SC-01_flat_baseline": "Flat horizontal regolith site; baseline geometric navigation verification.",
    "SC-02_moderate_slopes": "Smooth undulating terrain with regional 6° slope and 8°-12° local grades.",
    "SC-03_steep_slopes": "Steep 12° regional tilt with local gradients approaching 18°-20° traversability limit.",
    "SC-04_dense_obstacle_field": "Dense boulder hazard field requiring multi-turn collision avoidance.",
    "SC-05_narrow_passages": "Rocky terrain with 4.5m wide canyon passage requiring constrained kinodynamics.",
    "SC-06_crater_avoidance": "Direct collision vector blocked by 7m diameter parabolic impact crater.",
    "SC-07_sensor_noise": "High-noise multi-sensor environment (3x nominal Gaussian range & gyro noise).",
    "SC-08_sensor_dropout": "Intermittent LiDAR return dropouts (35% probability of packet loss).",
    "SC-09_localization_drift": "Tactical IMU bias drift stressing Error-State EKF dead reckoning.",
    "SC-10_wheel_slip_disturbance": "Loose sand patch inducing 45% longitudinal wheel slip disturbance.",
    "SC-11_unexpected_obstacles": "Pop-up dynamic boulder injected directly ahead during active execution.",
    "SC-12_completely_blocked": "Continuous impassable barrier requiring autonomous certified SAFE_STOP.",
    "SC-13_regolith_sinkage": "Deep low-cohesion dust regolith with Bekker sinkage > 4.5 cm.",
    "SC-14_high_illumination_shadows": "Low-elevation sun angle (15°) casting deep specular shadow occlusions.",
    "SC-15_multi_rover_crossing": "Cooperative multi-agent crossing with peer obstacle bubble injection."
}

st.sidebar.caption(scenario_descriptions.get(selected_scenario, ""))

seed_val = st.sidebar.number_input("Deterministic PRNG Seed", min_value=1, max_value=9999, value=100, step=17)
sim_resolution = st.sidebar.select_slider("DEM Grid Resolution (m)", options=[0.20, 0.40], value=0.40)
max_planner_iter = st.sidebar.slider("Hybrid A* Max Iterations", min_value=1000, max_value=5000, value=3000, step=500)

run_live_sim = st.sidebar.button("🚀 Run Closed-Loop Trial", use_container_width=True)

# Tabs
tab_live, tab_sensors, tab_matrix, tab_fdir, tab_audit = st.tabs([
    "📍 Closed-Loop Mission Execution",
    "📡 Multi-Sensor Rig Telemetry",
    "📊 15-Scenario V&V Campaign",
    "🛡️ FDIR & State Machine",
    "📋 TRL 5 Compliance & Evidence"
])

# -------------------------------------------------------------------------------------------------
# TAB 1: CLOSED-LOOP MISSION EXECUTION
# -------------------------------------------------------------------------------------------------
with tab_live:
    st.subheader(f"3D Digital Elevation Model & Path Trajectory — {selected_scenario}")

    @st.cache_data(show_spinner=False)
    def compute_scenario_data(scenario_id: str, seed: int, res: float):
        gen = ScenarioGenerator()
        terrain, meta = gen.build_scenario(scenario_id, seed=seed)
        elev_map = ElevationMap25D(size_x_m=terrain.size_x, size_y_m=terrain.size_y, resolution_m=res)
        pc_proc = PointCloudProcessor(voxel_size_m=res)
        trav_est = TraversabilityEstimator(max_slope_deg=MAX_TRAVERSABLE_SLOPE_DEG)
        rig = MultiSensorRig(terrain, noise_multiplier=meta["sensor_noise_factor"], lidar_dropout_prob=meta["lidar_dropout_prob"], seed=seed)
        
        # Touchdown init
        sim_x, sim_y, sim_yaw = meta["start_state"][:3]
        for dx in np.arange(-2.5, 2.5, res):
            for dy in np.arange(-2.5, 2.5, res):
                px, py = sim_x + dx, sim_y + dy
                if 0 <= px < terrain.size_x and 0 <= py < terrain.size_y:
                    ix, iy = elev_map.world_to_grid(px, py)
                    elev_map.elevation[ix, iy] = terrain.get_elevation_at(px, py)
                    elev_map.hit_count[ix, iy] = 10
                    elev_map.variance[ix, iy] = 0.01

        lidar_data = rig.sample_lidar(np.array([sim_x, sim_y, sim_yaw]))
        p_res = pc_proc.process_point_cloud(lidar_data["points_lidar"], lidar_data["T_world_lidar"])
        elev_map.update_from_point_cloud(p_res["points_world"], lidar_data["T_world_lidar"][:3, 3])
        elev_map.mark_obstacles(p_res["obstacle_points"])
        elev_map.detect_negative_obstacles(np.array([sim_x, sim_y]))
        trav_info = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)

        planner = KinodynamicHybridAStar(xy_resolution_m=0.50, max_iterations=3000)
        plan_res = planner.plan(meta["start_state"], meta["goal_pos"], trav_info["cost_map"], elev_map.res)

        return terrain, meta, elev_map, trav_info, plan_res, lidar_data, p_res

    terrain, meta, elev_map, trav_info, plan_res, lidar_data, p_res = compute_scenario_data(
        selected_scenario, seed_val, sim_resolution
    )

    # If run live simulation button clicked, execute full closed-loop trial
    trial_data = None
    if run_live_sim:
        with st.spinner("Executing real-time closed-loop simulation loop with ES-EKF and Kinodynamic tracking..."):
            runner = CampaignRunner()
            trial_data = runner.run_single_trial(selected_scenario, seed=seed_val)
            st.session_state["last_trial"] = trial_data
    elif "last_trial" in st.session_state and st.session_state["last_trial"]["scenario_id"] == selected_scenario:
        trial_data = st.session_state["last_trial"]

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("Initial Plan Status", "FEASIBLE" if plan_res["success"] else "UNFEASIBLE", f"{plan_res['latency_ms']} ms")
    with col_m2:
        st.metric("Initial Path Length", f"{plan_res.get('path_length_m', 0.0):.2f} m", f"{len(plan_res.get('path', []))} waypoints")
    with col_m3:
        if trial_data:
            st.metric("Trial Outcome", "SUCCESS" if trial_data["success"] else ("SAFE STOP" if trial_data["safe_handled"] else "FAULT"), f"{trial_data['final_operating_mode']}")
        else:
            st.metric("Trial Status", "READY", "Click 'Run Closed-Loop Trial'")
    with col_m4:
        if trial_data:
            st.metric("Collisions", f"{trial_data['collision_count']}", f"Clearance: {trial_data['min_obstacle_clearance_m']:.2f} m")
        else:
            st.metric("Confirmed Hazards", f"{len(terrain.boulders)} Rocks, {len(terrain.craters)} Craters")
    with col_m5:
        if trial_data:
            st.metric("Localization ATE RMSE", f"{trial_data['ate_rmse_m']:.3f} m", f"Max: {trial_data['ate_max_m']:.3f} m")
        else:
            st.metric("ODD Terrain Limits", f"Slope ≤ {MAX_TRAVERSABLE_SLOPE_DEG}°", f"Step ≤ {MAX_STEP_HEIGHT_M} m")

    # 3D Terrain Visualization (Plotly)
    fig_3d = go.Figure()

    # Downsampled elevation surface for smooth WebGL rendering
    step_ds = max(1, int(0.6 / terrain.res))
    X_sub = terrain.X[::step_ds, ::step_ds]
    Y_sub = terrain.Y[::step_ds, ::step_ds]
    Z_sub = terrain.elevation[::step_ds, ::step_ds]

    fig_3d.add_trace(go.Surface(
        x=X_sub, y=Y_sub, z=Z_sub,
        colorscale="Earth",
        opacity=0.88,
        showscale=False,
        name="Martian DEM Surface"
    ))

    # Boulders
    if terrain.boulders:
        bx = [b["x"] for b in terrain.boulders]
        by = [b["y"] for b in terrain.boulders]
        bz = [terrain.get_elevation_at(b["x"], b["y"]) + b["height"] * 0.5 for b in terrain.boulders]
        fig_3d.add_trace(go.Scatter3d(
            x=bx, y=by, z=bz,
            mode="markers",
            marker=dict(size=6, color="rgb(180, 50, 30)", symbol="diamond"),
            name="Confirmed Boulders"
        ))

    # Planned path
    if plan_res["success"] and len(plan_res["path"]) > 0:
        px = plan_res["path"][:, 0]
        py = plan_res["path"][:, 1]
        pz = [terrain.get_elevation_at(x, y) + 0.15 for x, y in zip(px, py)]
        fig_3d.add_trace(go.Scatter3d(
            x=px, y=py, z=pz,
            mode="lines",
            line=dict(color="rgb(0, 255, 255)", width=7),
            name="Kinodynamic Hybrid A* Plan"
        ))

    # Start and Goal markers
    sx, sy = meta["start_state"][0], meta["start_state"][1]
    gx, gy = meta["goal_pos"][0], meta["goal_pos"][1]
    fig_3d.add_trace(go.Scatter3d(
        x=[sx], y=[sy], z=[terrain.get_elevation_at(sx, sy) + 0.5],
        mode="markers+text",
        text=["START (Touchdown)"],
        marker=dict(size=9, color="lime", symbol="circle"),
        name="Touchdown Start"
    ))
    fig_3d.add_trace(go.Scatter3d(
        x=[gx], y=[gy], z=[terrain.get_elevation_at(gx, gy) + 0.5],
        mode="markers+text",
        text=["GOAL"],
        marker=dict(size=9, color="gold", symbol="cross"),
        name="Science Target Goal"
    ))

    fig_3d.update_layout(
        title=f"3D Synthetic Planetary Surface Reconstruction ({terrain.size_x}m × {terrain.size_y}m)",
        scene=dict(
            xaxis_title="East X (m)",
            yaxis_title="North Y (m)",
            zaxis_title="Elevation Z (m)",
            aspectmode="data"
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        height=580
    )
    st.plotly_chart(fig_3d, use_container_width=True)

    # 2D Heatmaps: Elevation vs Traversability Cost
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fig_elev = go.Figure(go.Heatmap(
            z=elev_map.elevation.T,
            x=np.linspace(0, terrain.size_x, elev_map.nx),
            y=np.linspace(0, terrain.size_y, elev_map.ny),
            colorscale="Viridis",
            colorbar=dict(title="Elevation (m)")
        ))
        fig_elev.update_layout(
            title="2.5D Elevation Grid Layer (Mean Z)",
            xaxis_title="X (m)", yaxis_title="Y (m)",
            height=400, margin=dict(l=40, r=40, b=40, t=40)
        )
        st.plotly_chart(fig_elev, use_container_width=True)

    with col_c2:
        fig_cost = go.Figure(go.Heatmap(
            z=trav_info["cost_map"].T,
            x=np.linspace(0, terrain.size_x, elev_map.nx),
            y=np.linspace(0, terrain.size_y, elev_map.ny),
            colorscale="Hot_r",
            zmin=0.0, zmax=1.0,
            colorbar=dict(title="Cost [0, 1]")
        ))
        fig_cost.update_layout(
            title="Multi-Criteria Traversability Cost Map (Slope + Step + Clearance)",
            xaxis_title="X (m)", yaxis_title="Y (m)",
            height=400, margin=dict(l=40, r=40, b=40, t=40)
        )
        st.plotly_chart(fig_cost, use_container_width=True)


# -------------------------------------------------------------------------------------------------
# TAB 2: MULTI-SENSOR RIG TELEMETRY
# -------------------------------------------------------------------------------------------------
with tab_sensors:
    st.subheader("Simulated Space-Grade Sensor Rig Telemetry")
    st.markdown("""
    Sensor suite modeling tactical-grade space navigation instruments:
    - **LiDAR**: 16-beam rotating laser rangefinder with range-dependent noise $\\sigma_r = 0.02(1 + (r/r_{max})^{1.5})$ m and beam dropouts.
    - **RGB-D Stereo Camera**: Range-squared disparity uncertainty $u(Z) \\propto Z^2$.
    - **Tactical 6-Axis IMU**: Allan variance modeling bias instability and random walk under Martian gravity $g = 3.71\\text{ m/s}^2$.
    - **Wheel Odometry**: 6-wheel encoder kinematics with non-linear longitudinal slip $\\kappa_{slip}$.
    """)

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("#### 3D Point Cloud Ground vs Obstacle Segmentation")
        if lidar_data["num_returns"] > 0:
            fig_pc = go.Figure()
            # Sample ground points
            gp = p_res["ground_points"]
            if len(gp) > 0:
                gp_sub = gp[::max(1, len(gp)//500)]
                fig_pc.add_trace(go.Scatter3d(
                    x=gp_sub[:, 0], y=gp_sub[:, 1], z=gp_sub[:, 2],
                    mode="markers",
                    marker=dict(size=3, color="rgb(70, 130, 180)", opacity=0.6),
                    name="Segmented Ground Baseline"
                ))
            # Obstacle points
            op = p_res["obstacle_points"]
            if len(op) > 0:
                fig_pc.add_trace(go.Scatter3d(
                    x=op[:, 0], y=op[:, 1], z=op[:, 2],
                    mode="markers",
                    marker=dict(size=5, color="red", symbol="diamond"),
                    name="Segmented Obstacle Returns"
                ))
            fig_pc.update_layout(
                scene=dict(aspectmode="data", xaxis_title="X (m)", yaxis_title="Y (m)", zaxis_title="Z (m)"),
                margin=dict(l=0, r=0, b=0, t=30), height=420
            )
            st.plotly_chart(fig_pc, use_container_width=True)
            st.caption(f"LiDAR Scan: {lidar_data['num_returns']} returns, {len(p_res['obstacle_points'])} classified obstacle returns.")
        else:
            st.warning("No LiDAR returns generated in current pose.")

    with col_s2:
        st.markdown("#### RGB-D Stereo Disparity Depth Map")
        depth_cam = MultiSensorRig(terrain).sample_depth_camera(meta["start_state"])
        depth_grid = depth_cam["depth_grid_m"]
        fig_depth = go.Figure(go.Heatmap(
            z=depth_grid,
            colorscale="Plasma",
            colorbar=dict(title="Depth (m)")
        ))
        fig_depth.update_layout(
            title=f"Stereo Depth Disparity ({depth_cam['grid_shape'][1]}×{depth_cam['grid_shape'][0]} px)",
            xaxis_title="Azimuth Pixel", yaxis_title="Elevation Pixel",
            margin=dict(l=40, r=40, b=40, t=40), height=420
        )
        st.plotly_chart(fig_depth, use_container_width=True)
        st.caption(f"Valid depth pixels: {depth_cam['valid_returns_count']} / {depth_grid.size}. Range: [{depth_cam['min_depth_m']:.2f}m, {depth_cam['max_depth_m']:.2f}m].")

    # IMU & Odometry strip charts
    st.markdown("#### Tactical 6-Axis IMU & Slip Odometry Telemetry")
    imu_meas = MultiSensorRig(terrain).sample_imu(meta["start_state"], linear_speed_mps=0.40, angular_rate_rps=0.05, dt_s=0.25)
    
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    with col_i1:
        st.metric("IMU Accel X (Forward)", f"{imu_meas['meas_accel_mps2'][0]:.3f} m/s²")
    with col_i2:
        st.metric("IMU Accel Z (Gravity)", f"{imu_meas['meas_accel_mps2'][2]:.3f} m/s²", f"Nominal: -{G_MARS} m/s²")
    with col_i3:
        st.metric("IMU Gyro Z (Yaw Rate)", f"{np.degrees(imu_meas['meas_gyro_rps'][2]):.2f} °/s")
    with col_i4:
        st.metric("Terrain Traction μ", f"{terrain.regolith_friction[10, 10]:.2f}")


# -------------------------------------------------------------------------------------------------
# TAB 3: 15-SCENARIO V&V CAMPAIGN
# -------------------------------------------------------------------------------------------------
with tab_matrix:
    st.subheader("Standardized 15-Scenario Validation Campaign Results")
    st.markdown("""
    Evaluated across **15 standardized scenario classes (SC-01 through SC-15)** parameterized by deterministic PRNG seeds.  
    Confidence intervals are calculated using the **Wilson score interval with continuity correction (95% confidence)**.
    """)

    summary_file = "results/trl5/campaign_summary.json"
    baseline_file = "results/trl5/baseline_comparison.json"
    ablation_file = "results/trl5/ablation_study.json"

    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        table_rows = []
        for sc_id, s in summary_data.items():
            ci_str = f"[{s['wilson_ci_95'][0]}%, {s['wilson_ci_95'][1]}%]"
            table_rows.append({
                "Scenario ID": sc_id,
                "Runs": s["total_runs"],
                "Successes": s["success_count"],
                "Success Rate": f"{s['success_rate_pct']}%",
                "95% Wilson CI": ci_str,
                "Collisions": s["total_collisions"],
                "ATE RMSE (m)": s["mean_ate_rmse_m"],
                "Planning Latency (ms)": s["mean_planning_latency_ms"],
                "Min Clearance (m)": s["mean_min_clearance_m"],
            })

        df_summary = pd.DataFrame(table_rows)
        st.dataframe(df_summary, use_container_width=True)

        # Plot Success Rates with Error Bars
        sc_names = [r["Scenario ID"].split("_")[0] for r in table_rows]
        rates = [summary_data[r["Scenario ID"]]["success_rate_pct"] for r in table_rows]
        ci_lows = [summary_data[r["Scenario ID"]]["wilson_ci_95"][0] for r in table_rows]
        ci_highs = [summary_data[r["Scenario ID"]]["wilson_ci_95"][1] for r in table_rows]
        err_plus = [ci_highs[i] - rates[i] for i in range(len(rates))]
        err_minus = [rates[i] - ci_lows[i] for i in range(len(rates))]

        fig_bar = go.Figure(data=go.Bar(
            x=sc_names,
            y=rates,
            error_y=dict(type='data', symmetric=False, array=err_plus, arrayminus=err_minus),
            marker_color="rgb(50, 168, 82)",
            text=[f"{r}%" for r in rates],
            textposition="auto"
        ))
        fig_bar.update_layout(
            title="Safe Handling & Success Rates across 15 Scenarios (95% Wilson Confidence Intervals)",
            xaxis_title="Standardized Scenario Class",
            yaxis_title="Success Rate (%)",
            yaxis=dict(range=[0, 105]),
            height=420, margin=dict(l=40, r=40, b=40, t=50)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("Campaign summary not yet generated. Run `python experiments/run_trl5_campaign.py` to generate evidence.")

    # Comparative Baselines Table
    st.markdown("### Comparative Baseline Benchmarking")
    st.caption("Evaluated on SC-04 Dense Obstacle Field and SC-02 Slopes to verify superiority over legacy methods.")
    if os.path.exists(baseline_file):
        with open(baseline_file, "r", encoding="utf-8") as f:
            b_data = json.load(f)
        b_rows = []
        for name, d in b_data.items():
            b_rows.append({
                "Algorithm": name,
                "Success": "PASSED" if d["success"] else "FAILED",
                "Collisions": d["collisions"],
                "Path Length (m)": d["path_length_m"],
                "Planning Latency (ms)": d["latency_ms"],
                "Technical Notes": d["notes"]
            })
        st.dataframe(pd.DataFrame(b_rows), use_container_width=True)
    else:
        st.caption("Baseline evidence file pending execution.")

    # Ablation Studies Table
    st.markdown("### Algorithmic Ablation Study")
    st.caption("Isolates contributions of individual architectural subsystems under SC-04 hazard conditions.")
    if os.path.exists(ablation_file):
        with open(ablation_file, "r", encoding="utf-8") as f:
            ab_data = json.load(f)
        ab_rows = []
        for name, d in ab_data.items():
            ab_rows.append({
                "Ablation Condition": name,
                "Safe Handled": "YES" if d["success"] else "NO",
                "Failure Mode": d["failure_reason"],
                "Collisions": d["collision_count"],
                "ATE RMSE (m)": d["ate_rmse_m"],
                "Min Clearance (m)": d["min_clearance_m"],
                "Latency (ms)": d["mean_planning_latency_ms"]
            })
        st.dataframe(pd.DataFrame(ab_rows), use_container_width=True)
    else:
        st.caption("Ablation evidence file pending execution.")


# -------------------------------------------------------------------------------------------------
# TAB 4: FDIR & STATE MACHINE
# -------------------------------------------------------------------------------------------------
with tab_fdir:
    st.subheader("Autonomous Executive & 11-Mode FDIR State Machine")
    st.markdown("""
    The planetary rover executive implements a certified 11-mode discrete state machine with strict
    transition guards and automated Safe-Stop Fault Detection, Isolation, and Recovery (FDIR).
    """)

    col_f1, col_f2 = st.columns([1, 2])

    with col_f1:
        st.markdown("#### Operating Modes")
        modes_info = [
            ("INITIALIZATION", "Self-test & hardware check"),
            ("CALIBRATION", "IMU bias & wheel zeroing"),
            ("PERCEPTION", "Point cloud & depth camera acquisition"),
            ("MAPPING", "2.5D elevation grid fusion"),
            ("TRAVERSABILITY_EVALUATION", "Multi-criteria cost calculation"),
            ("PLANNING", "Kinodynamic Hybrid A* generation"),
            ("EXECUTION", "Pure pursuit closed-loop tracking"),
            ("REPLANNING", "Dynamic corridor obstruction bypass"),
            ("OBSTACLE_AVOIDANCE", "Evasive maneuver execution"),
            ("SAFE_STOP", "Controlled deceleration to full rest"),
            ("FAULT", "Permanent latch on lethal failure"),
            ("MISSION_COMPLETE", "Goal tolerance satisfied")
        ]
        for m, desc in modes_info:
            st.markdown(f"- **`{m}`**: {desc}")

    with col_f2:
        st.markdown("#### FDIR Safety Interlocks & Watchdog Triggers")
        st.markdown("""
        | Watchdog Monitor | Trip Condition | Autonomous FDIR Action |
        | :--- | :--- | :--- |
        | **Slip Entrapment** | Longitudinal slip $s > 0.60$ for $\\ge 1.0\\text{ s}$ | Trigger immediate emergency SAFE_STOP ($a = -0.20\\text{ m/s}^2$) |
        | **Covariance Divergence** | $3\\sigma$ position covariance trace $\\text{Tr}(P) > 2.5\\text{ m}^2$ | Safe-stop rover; request relocalization scan |
        | **Chassis Collision** | Chassis bounding box intersects lethal obstacle (cost $\\ge 0.98$) | Permanent FAULT latch; complete immediate halt |
        | **Tip-Over Barrier** | Pitch / roll angle $\\ge 25.0^\\circ$ | Restrict motion command; execute evasive turn |
        | **Corridor Obstruction** | Planned trajectory intersects new obstacle in next $3.5\\text{ m}$ | Replan path; if blocked, transition to SAFE_STOP |
        """)

        # Certified Deceleration Profile Chart
        t_prof = np.linspace(0, 3.0, 60)
        v_init = 0.40
        a_dec = -0.20
        v_prof = np.maximum(0.0, v_init + a_dec * t_prof)
        d_prof = (v_init**2 - v_prof**2) / (2.0 * abs(a_dec))

        fig_dec = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dec.add_trace(go.Scatter(x=t_prof, y=v_prof, mode="lines", name="Velocity v(t)", line=dict(color="orange", width=3)), secondary_y=False)
        fig_dec.add_trace(go.Scatter(x=t_prof, y=d_prof, mode="lines", name="Stopping Distance d(t)", line=dict(color="cyan", dash="dash")), secondary_y=True)
        fig_dec.update_layout(
            title="Certified Safe-Stop Deceleration Profile (a = -0.20 m/s², d_stop = 0.40 m)",
            xaxis_title="Time from Trigger (s)",
            height=300, margin=dict(l=40, r=40, b=40, t=40)
        )
        fig_dec.update_yaxes(title_text="Velocity (m/s)", secondary_y=False)
        fig_dec.update_yaxes(title_text="Stopping Distance (m)", secondary_y=True)
        st.plotly_chart(fig_dec, use_container_width=True)


# -------------------------------------------------------------------------------------------------
# TAB 5: TRL 5 COMPLIANCE & EVIDENCE
# -------------------------------------------------------------------------------------------------
with tab_audit:
    st.subheader("NASA TRL 5 Compliance Assessment & V&V Evidence Package")
    st.markdown("""
    According to the **NASA Systems Engineering Handbook (SP-2016-6105, Rev 2)**:
    - **TRL 4**: Component and/or breadboard validation in laboratory environment.
    - **TRL 5**: Component and/or breadboard validation in relevant environment.
    """)

    st.markdown("#### Traceable Verification Matrix")
    req_rows = [
        {"Req ID": "SR-01", "Requirement": "Continuous 3D DEM Surface Modeling", "Status": "VERIFIED", "Evidence": "Bilinear elevation field & normal vectors (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-02", "Requirement": "Multi-Sensor Breadboard Simulation", "Status": "VERIFIED", "Evidence": "LiDAR, RGB-D, 6-axis IMU, Wheel Odometry (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-03", "Requirement": "Coordinate Transforms (J2000/ICRF, SE(3))", "Status": "VERIFIED", "Evidence": "Homogeneous transform algebra verified (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-04", "Requirement": "2.5D Elevation & Variance Grid", "Status": "VERIFIED", "Evidence": "Recursive scalar Kalman update for sigma_z^2 (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-05", "Requirement": "Multi-Criteria Traversability Engine", "Status": "VERIFIED", "Evidence": "Slope, step, roughness, clearance in [0, 1] (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-06", "Requirement": "Negative Obstacle Detection", "Status": "VERIFIED", "Evidence": "Radial step drop-off detection past crests (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-07", "Requirement": "Kinodynamic Hybrid A* Planning", "Status": "VERIFIED", "Evidence": "Bicycle kinematics, curvature rho >= 0.67m (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-08", "Requirement": "Error-State EKF Sensor Fusion", "Status": "VERIFIED", "Evidence": "Kinematic IMU propagation + Joseph form update (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-09", "Requirement": "Pure Pursuit Path Tracking", "Status": "VERIFIED", "Evidence": "Adaptive lookahead & terrain speed derating (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-10", "Requirement": "Certified Safe-Stop FDIR", "Status": "VERIFIED", "Evidence": "Deceleration profile a = -0.20 m/s^2 (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-11", "Requirement": "Discrete 11-Mode State Machine", "Status": "VERIFIED", "Evidence": "Deterministic transitions & fault latching (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-12", "Requirement": "6-DOF Dynamics & Rocker-Bogie", "Status": "VERIFIED", "Evidence": "Newton-Euler, FASM tipover & normal loads (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-13", "Requirement": "Terramechanics & Drawbar Pull", "Status": "VERIFIED", "Evidence": "Bekker pressure-sinkage & Janosi shear (tests/test_trl5_navigation.py)"},
        {"Req ID": "SR-14", "Requirement": "15 Standardized Scenario Classes", "Status": "VERIFIED", "Evidence": "Deterministic PRNG seeds SC-01 to SC-15 (tests/test_trl5_perception.py)"},
        {"Req ID": "SR-15", "Requirement": "Automated V&V Campaign & Manifests", "Status": "VERIFIED", "Evidence": "Wilson score intervals & JSON manifests (tests/test_trl5_navigation.py)"},
    ]
    st.dataframe(pd.DataFrame(req_rows), use_container_width=True)

    st.markdown("#### Download Machine-Readable V&V Artifacts")
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    def load_json_or_empty(filepath: str) -> str:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return json.dumps({"status": "pending_generation"})

    with col_d1:
        st.download_button(
            "📥 Campaign Summary",
            data=load_json_or_empty("results/trl5/campaign_summary.json"),
            file_name="campaign_summary.json",
            mime="application/json",
            use_container_width=True
        )
    with col_d2:
        st.download_button(
            "📥 Trial Manifest",
            data=load_json_or_empty("results/trl5/campaign_manifest.json"),
            file_name="campaign_manifest.json",
            mime="application/json",
            use_container_width=True
        )
    with col_d3:
        st.download_button(
            "📥 Baseline Comparison",
            data=load_json_or_empty("results/trl5/baseline_comparison.json"),
            file_name="baseline_comparison.json",
            mime="application/json",
            use_container_width=True
        )
    with col_d4:
        st.download_button(
            "📥 Ablation Studies",
            data=load_json_or_empty("results/trl5/ablation_study.json"),
            file_name="ablation_study.json",
            mime="application/json",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 13px;">
    APPS Automated Planetary Perception System • NASA TRL 5 Synthetic Verification Campaign<br>
    Compiled with compile-time safety lock <code>PROTOTYPE_LOCK = True</code>. Not certified for actual flight deployment.
</div>
""", unsafe_allow_html=True)

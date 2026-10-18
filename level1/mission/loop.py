"""Level 1 Closed-Loop Mission Execution Loop.
Part 6 Appendix AM, Part 8 Chapter 127 (Tasks 44 & 64).
"""
import numpy as np
from scipy import ndimage as ndi
from level1.sensing.sensor_model import believed_pose, register
from level1.navigation.cost_map import cell_cost, blocked_map, inflate
from level1.navigation.planner_v2 import plan_J
from level1.navigation.route_audit import route_audit
from level1.navigation.monitors import discrepancy, Watchdog


def run_mission(simulator, cfg: dict, rng, start: tuple,
                known_map: np.ndarray = None, sensor_fail: tuple = (), max_steps: int = 300) -> dict:
    """Execute complete closed-loop mission with information boundary, watchdog, and route audits.
    
    Returns summary dict:
        outcome: 'success' | 'collision' | 'no_path' | 'rejected' | 'safe_stop' | 'timeout'
        reason: str
        steps: int
        log: list
        discovered: int
        collided: bool
    """
    n = simulator.n
    w = cfg["w"]
    wd = Watchdog(**cfg.get("wd", {}))
    
    # Internal rover belief state
    est = np.zeros((n, n), bool) if known_map is None else known_map.copy()
    seen = np.zeros((n, n), bool) if known_map is None else np.ones((n, n), bool)
    unc = np.where(seen, 0.10, 1.0)
    
    pos = start
    hd = 0.0
    log = []
    disc = 0
    last_path = None
    scans = 0

    def end(outcome, t, collided=False, reason=None):
        return dict(
            outcome=outcome,
            reason=reason,
            steps=t,
            log=log,
            discovered=disc,
            collided=collided
        )

    for t in range(max_steps):
        sensor_ok = (t not in sensor_fail)
        
        # 1. Believed pose = true pose + pose error
        bp = believed_pose(pos, cfg.get("pose_sigma", 0.0), rng, n)
        
        # 2. Observe strictly through sensor model
        if cfg.get("sense", True):
            u_raw, obs_raw, uo = simulator.get_observation(pos, hd, cfg["sensor"], rng, sensor_ok)
        else:
            u_raw = np.zeros((n, n), bool)
            obs_raw = np.zeros((n, n), bool)
            uo = np.ones((n, n), dtype=float)
            
        # 3. Register into believed frame
        sh = (bp[0] - pos[0], bp[1] - pos[1])
        u_reg = register(u_raw, sh)
        obs_reg = register(obs_raw, sh)
        
        # 4. Compare with map held before (discrepancy)
        d_new, d_clear = discrepancy(est, seen, u_reg, obs_reg)
        
        # 5. Fuse into belief map
        if cfg.get("fuse", "union") == "union":
            est = est | (u_reg & obs_reg)
        else:
            est = np.where(obs_reg, u_reg, est)
            
        seen |= obs_reg
        unc = np.where(obs_reg, uo, unc)
        
        # 6. Build risk, uncertainty, and cost fields
        risk = est.astype(float)
        cost = cell_cost(risk, unc, 0.0, w)
        
        # 7. Build blocked map and apply footprint inflation if requested
        blk = blocked_map(risk, unc, seen, w, allow_unknown=cfg.get("allow_unknown", False))
        if cfg.get("footprint_radius", 0) > 0:
            blk = inflate(blk, cfg["footprint_radius"])
        blk[bp[0], bp[1]] = False
        
        # 8. Frontier expansion candidate identification
        fr = ndi.binary_dilation(~seen, np.ones((3, 3), bool)) & seen & ~est
        
        # 9. Plan route
        pl = plan_J(
            cost=cost,
            blocked=blk,
            start=bp,
            goal_col=n - 1,
            risk=risk,
            p_budget=w.get("p_budget", 0.50),
            h_weight=cfg.get("h_weight", 1.80),
            frontier=fr,
            allow_corner_cutting=cfg.get("corner_cutting", True)
        )
        
        log.append(dict(
            t=t,
            pos=pos,
            believed=bp,
            status=pl["status"],
            new_unsafe=d_new,
            sensor_ok=sensor_ok,
            heading=round(hd, 2)
        ))
        
        if pl["status"] != "ok":
            return end("rejected" if pl["status"] == "rejected_budget" else "no_path", t)
            
        # 10. Check route invalidation (Obstacle Discovery)
        inval = False
        if last_path is not None and len(last_path) > 1:
            inval = any(blk[c[0], c[1]] for c in last_path[1:])
            disc += int(inval)
            
        # 11. Independent Route Audit
        bad = route_audit(pl["path"], blk)
        if bad:
            return end("safe_stop", t, reason=f"audit: {bad[0]}")
            
        # 12. Run Watchdog
        stop_reason = wd.update(bp[1], sensor_ok, inval)
        if stop_reason:
            return end("safe_stop", t, reason=stop_reason)
            
        last_path = pl["path"]
        
        # 13. Move or Scan
        if len(pl["path"]) == 1:
            # Trapped / nowhere better to go -> turn in place to scan
            if scans >= cfg.get("scan_limit", 4):
                return end("safe_stop", t, reason="no_move")
            scans += 1
            hd += cfg.get("scan_step", float(np.radians(45.0)))
            continue
            
        # Execute single move step
        nxt = pl["path"][1]
        mv = (nxt[0] - bp[0], nxt[1] - bp[1])
        pos = (pos[0] + mv[0], pos[1] + mv[1])
        hd = float(np.arctan2(mv[0], mv[1]))
        
        # Invariant checks against ground truth
        if not simulator.in_bounds(pos):
            return end("safe_stop", t, reason="left_map")
            
        if simulator.is_hazard(pos):
            return end("collision", t + 1, collided=True)
            
        if simulator.is_goal(pos):
            return end("success", t + 1)

    return end("timeout", max_steps)

"""Level 1 Route Optimization Planner with Risk Budgeting and Admissible Heuristic.
Part 6 Appendix AK, Part 8 Chapter 129 (Tasks 43 & 61).
"""
import heapq
import math
import numpy as np

MOVES = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def octile_distance(u: tuple, v: tuple) -> float:
    dy, dx = abs(u[0] - v[0]), abs(u[1] - v[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)


def plan_J(cost: np.ndarray, blocked: np.ndarray, start: tuple, goal_col: int,
           risk: np.ndarray = None, p_budget: float = 0.50, h_weight: float = 0.0,
           frontier: np.ndarray = None, allow_corner_cutting: bool = True, use_heuristic: bool = False):
    """Multi-criteria grid path planner.
    Scored by J(path) = sum_k L_k * 0.5 * (c_k + c_{k+1}).
    
    Returns dict(status, path, J, p_proxy):
        status: 'ok' | 'no_path' | 'rejected_budget' | 'invalid_input'
    """
    if cost is None or blocked is None:
        return dict(status="invalid_input", path=None, J=None, p_proxy=None)
    n = cost.shape[0]
    if not (0 <= start[0] < n and 0 <= start[1] < n) or blocked[start]:
        return dict(status="invalid_input", path=None, J=None, p_proxy=None)
    if not np.isfinite(cost).all() or (cost < 0).any():
        return dict(status="invalid_input", path=None, J=None, p_proxy=None)

    # Multi-source / Priority Queue
    # Entry: (priority, counter, cost_so_far, node)
    counter = 0
    min_cost = max(cost.min(), 1e-4)
    g = {start: 0.0}
    par = {}
    done = {}
    
    h0 = 0.0
    if use_heuristic:
        h0 = (goal_col - start[1]) * min_cost
    pq = [(h0, counter, 0.0, start)]
    
    while pq:
        prio, _, c0, u = heapq.heappop(pq)
        if c0 > g.get(u, 1e18):
            continue
        done[u] = c0
        
        # Goal check when not using frontier heuristic
        if h_weight == 0.0 and u[1] == goal_col:
            break
            
        for dy, dx in MOVES:
            v = (u[0] + dy, u[1] + dx)
            if 0 <= v[0] < n and 0 <= v[1] < n and not blocked[v]:
                # Corner-cutting prevention
                if not allow_corner_cutting and dy != 0 and dx != 0:
                    if blocked[u[0] + dy, u[1]] or blocked[u[0], u[1] + dx]:
                        continue
                        
                L = math.sqrt(2.0) if (dy and dx) else 1.0
                c = c0 + L * 0.5 * (cost[u] + cost[v])
                if c < g.get(v, 1e18):
                    g[v] = c
                    par[v] = u
                    counter += 1
                    h = (goal_col - v[1]) * min_cost if use_heuristic else 0.0
                    heapq.heappush(pq, (c + h, counter, c, v))

    # Target selection
    if h_weight > 0.0:
        # Frontier target selector
        tgt = min(done, key=lambda u: (done[u] + h_weight * (n - 1 - u[1]), u[0], u[1]))
        if tgt == start and frontier is not None:
            fc = [u for u in done if frontier[u] and u != start]
            if fc:
                tgt = min(fc, key=lambda u: (done[u] + 0.5 * h_weight * (n - 1 - u[1]), u[0], u[1]))
    else:
        cand = [u for u in done if u[1] == goal_col]
        if not cand:
            return dict(status="no_path", path=None, J=None, p_proxy=None)
        tgt = min(cand, key=lambda u: (done[u], u[0]))

    # Reconstruct path
    p = [tgt]
    while p[-1] in par:
        p.append(par[p[-1]])
    p = p[::-1]

    # Evaluate route risk budget
    pp = None
    if risk is not None:
        pp = float(1.0 - np.prod([1.0 - risk[q] for q in p[1:]])) if len(p) > 1 else 0.0
        if pp > p_budget:
            return dict(status="rejected_budget", path=None, J=done[tgt], p_proxy=pp)

    return dict(status="ok", path=p, J=done[tgt], p_proxy=pp)

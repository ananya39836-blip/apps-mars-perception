"""2D Closed-loop Simulator for testing perception inside an autonomous decision loop.
Chapter 72, Appendix AC (Part 5) - Task 35.
"""
import heapq
import numpy as np

MOVES = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def plan(blocked: np.ndarray, start: tuple, goal_col: int):
    """Dijkstra on an 8-connected grid from start to any cell in goal_col. None if no route."""
    n = blocked.shape[0]
    g = {start: 0.0}
    par = {}
    pq = [(0.0, start)]
    while pq:
        c0, u = heapq.heappop(pq)
        if c0 > g.get(u, 1e18):
            continue
        if u[1] == goal_col:
            p = [u]
            while u in par:
                u = par[u]
                p.append(u)
            return p[::-1]
        for dy, dx in MOVES:
            v = (u[0] + dy, u[1] + dx)
            if 0 <= v[0] < n and 0 <= v[1] < n and not blocked[v]:
                c = c0 + (1.414 if dy and dx else 1.0)
                if c < g.get(v, 1e18):
                    g[v] = c
                    par[v] = u
                    heapq.heappush(pq, (c, v))
    return None


def run_episode(truth: np.ndarray, perceive, start_row: int, rng,
                allow_unknown: bool = False, fuse: str = "union", max_steps: int = 400):
    """Closed-loop episode on a cell grid.
    truth: bool hazard grid (evaluation only).
    perceive(truth, pos, rng) -> (unsafe_estimate, observed_mask), both grids; the rover
    never sees truth.
    fuse='union' keeps a cell unsafe once any frame called it unsafe; 'latest' trusts newest frame.
    Unknown (never observed) cells are blocked unless allow_unknown.
    Outcomes: 'success', 'collision', 'no_path', 'timeout'.
    """
    n = truth.shape[0]
    est = np.zeros((n, n), bool)
    seen = np.zeros((n, n), bool)
    pos = (start_row, 0)
    steps = replans = 0
    last = None

    while steps < max_steps:
        u, obs = perceive(truth, pos, rng)
        est = (est | (u & obs)) if fuse == "union" else np.where(obs, u, est)
        seen |= obs
        blocked = est | ((~seen) & (not allow_unknown))
        blocked[pos] = False

        path = plan(blocked, pos, n - 1)
        if path is None:
            return dict(outcome="no_path", steps=steps, replans=replans)
        if last is not None and path[:len(last)] != last[:len(path)] and path != last:
            replans += 1
        last = path[1:]
        if len(path) == 1:
            return dict(outcome="success", steps=steps, replans=replans)
        pos = path[1]
        steps += 1
        if truth[pos]:
            return dict(outcome="collision", steps=steps, replans=replans)
        if pos[1] == n - 1:
            return dict(outcome="success", steps=steps, replans=replans)

    return dict(outcome="timeout", steps=steps, replans=replans)

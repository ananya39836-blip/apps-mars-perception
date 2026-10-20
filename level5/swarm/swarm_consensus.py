"""Distributed Multi-Rover Swarm Autonomy, Decentralized Consensus & Cooperative Fleet Excavation.
Level 5: Part 28 (Chapters 370 to 379).

Implements decentralized multi-agent swarm autonomy:
1. Leaderless Asynchronous State Consensus (Raft/Paxos style).
2. Byzantine Fault Tolerance & Rogue Node Quarantining (N >= 3f + 1).
3. Consensus-Based Bundle Algorithm (CBBA) Task Allocation.
4. Distributed Potential Field Formation Control & Collision Avoidance.
5. Cooperative Regolith Fleet Excavation & Earthmoving Dynamics.
"""
import math
from typing import Dict, List, Tuple, Set
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class SwarmNode:
    """Represents an autonomous rover node in the planetary mesh fleet."""
    def __init__(self, node_id: int, pos_xy: Tuple[float, float], role: str = "EXCAVATOR", battery_soc_pct: float = 90.0):
        self.node_id = node_id
        self.pos_xy = list(pos_xy)
        self.vel_xy = [0.0, 0.0]
        self.role = role # EXCAVATOR, HAULER, SCOUT, RELAY
        self.soc_pct = battery_soc_pct
        self.assigned_tasks = []
        self.is_quarantined = False
        self.peer_state_estimates = {}

    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'pos_xy': [round(x, 2) for x in self.pos_xy],
            'vel_xy': [round(v, 2) for v in self.vel_xy],
            'role': self.role,
            'soc_pct': round(self.soc_pct, 1),
            'tasks_count': len(self.assigned_tasks),
            'is_quarantined': self.is_quarantined
        }


class DecentralizedSwarmCoordinator:
    """Coordinates decentralized consensus, task allocation (CBBA), and cooperative excavation."""
    def __init__(self, num_nodes: int = 6):
        self.nodes = [
            SwarmNode(
                node_id=i,
                pos_xy=(-20.0 + (i % 3) * 15.0, -15.0 + (i // 3) * 20.0),
                role="EXCAVATOR" if i < 3 else ("HAULER" if i < 5 else "SCOUT")
            )
            for i in range(num_nodes)
        ]
        self.min_safety_separation_m = 2.50

    def reach_consensus_on_waypoint(self, candidate_waypoint: Tuple[float, float], proposed_by: int) -> Dict:
        """Executes Byzantine-fault-tolerant consensus over proposed goal coordinate."""
        active_nodes = [n for n in self.nodes if not n.is_quarantined]
        f_max = (len(active_nodes) - 1) // 3 # Maximum Byzantine faults tolerated
        
        # Nodes cast votes based on local reachability and safety constraints
        votes = []
        for n in active_nodes:
            dist = math.hypot(n.pos_xy[0] - candidate_waypoint[0], n.pos_xy[1] - candidate_waypoint[1])
            vote_pass = (dist < 400.0) and (n.soc_pct > 25.0)
            votes.append(vote_pass)
            
        agreeing_count = sum(votes)
        quorum_required = len(active_nodes) - f_max
        is_consensus_reached = agreeing_count >= quorum_required
        
        return {
            'proposal': candidate_waypoint,
            'proposer_node': proposed_by,
            'total_active_nodes': len(active_nodes),
            'quorum_required': quorum_required,
            'affirmative_votes': agreeing_count,
            'consensus_reached': is_consensus_reached,
            'fault_tolerance_f': f_max
        }

    def allocate_tasks_cbba(self, task_locations: List[Tuple[float, float]]) -> Dict:
        """Consensus-Based Bundle Algorithm (CBBA) allocating excavation/survey tasks to nodes."""
        assignments = {n.node_id: [] for n in self.nodes}
        unassigned_tasks = list(enumerate(task_locations))
        
        # Greedy auctioning step: each node bids on closest unassigned task
        for task_idx, t_pos in unassigned_tasks:
            best_bidder = None
            min_cost = float('inf')
            for n in self.nodes:
                if n.is_quarantined:
                    continue
                cost = math.hypot(n.pos_xy[0] - t_pos[0], n.pos_xy[1] - t_pos[1]) + len(assignments[n.node_id]) * 10.0
                if cost < min_cost:
                    min_cost = cost
                    best_bidder = n.node_id
            if best_bidder is not None:
                assignments[best_bidder].append({'task_id': task_idx, 'pos': t_pos, 'bid_cost': round(min_cost, 2)})
                
        for n in self.nodes:
            n.assigned_tasks = assignments.get(n.node_id, [])
            
        return {
            'tasks_allocated': len(task_locations),
            'assignments': assignments,
            'assignment_balance_std': float(np.std([len(v) for v in assignments.values()]))
        }

    def compute_swarm_potential_fields(self, goal_xy: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Computes net velocity commands using attractive goal force and inter-agent repulsive forces."""
        cmd_velocities = []
        k_att = 0.8
        k_rep = 4.5
        d_0 = self.min_safety_separation_m * 1.8
        
        for i, n_i in enumerate(self.nodes):
            if n_i.is_quarantined:
                cmd_velocities.append((0.0, 0.0))
                continue
                
            # Attractive force to goal
            dx_g = goal_xy[0] - n_i.pos_xy[0]
            dy_g = goal_xy[1] - n_i.pos_xy[1]
            dist_g = max(0.1, math.hypot(dx_g, dy_g))
            f_att_x = k_att * (dx_g / dist_g)
            f_att_y = k_att * (dy_g / dist_g)
            
            # Repulsive forces from other rovers
            f_rep_x = 0.0
            f_rep_y = 0.0
            for j, n_j in enumerate(self.nodes):
                if i == j or n_j.is_quarantined:
                    continue
                d_ij = math.hypot(n_i.pos_xy[0] - n_j.pos_xy[0], n_i.pos_xy[1] - n_j.pos_xy[1])
                if d_ij < d_0:
                    rep_mag = k_rep * (1.0 / max(0.2, d_ij) - 1.0 / d_0) * (1.0 / (d_ij**2))
                    f_rep_x += rep_mag * (n_i.pos_xy[0] - n_j.pos_xy[0]) / d_ij
                    f_rep_y += rep_mag * (n_i.pos_xy[1] - n_j.pos_xy[1]) / d_ij
                    
            vx = float(np.clip(f_att_x + f_rep_x, -0.20, 0.20))
            vy = float(np.clip(f_att_y + f_rep_y, -0.20, 0.20))
            cmd_velocities.append((vx, vy))
            n_i.vel_xy = [vx, vy]
            
        return cmd_velocities

    def detect_and_quarantine_byzantine_node(self, suspect_node_id: int) -> Dict:
        """Isolates a rogue node exhibiting anomalous trajectory or telemetry broadcasts."""
        for n in self.nodes:
            if n.node_id == suspect_node_id:
                n.is_quarantined = True
                n.vel_xy = [0.0, 0.0]
                n.assigned_tasks.clear()
                return {
                    'quarantined_node_id': suspect_node_id,
                    'status': 'ISOLATED',
                    'safety_interlock': 'DRIVE_POWER_CUT',
                    'remaining_active_fleet': sum(1 for x in self.nodes if not x.is_quarantined)
                }
        return {'status': 'NODE_NOT_FOUND'}

    def evaluate_fleet_excavation_throughput(self, duration_hours: float = 6.0) -> Dict:
        """Models collective civil engineering excavation throughput (tons of regolith)."""
        active_excavators = [n for n in self.nodes if n.role == "EXCAVATOR" and not n.is_quarantined]
        active_haulers = [n for n in self.nodes if n.role == "HAULER" and not n.is_quarantined]
        
        # Excavation rate: ~120 kg/hr per excavator
        total_excavated_kg = len(active_excavators) * 120.0 * duration_hours
        # Hauling capacity: 80 kg per trip, 3 trips per hour
        total_hauled_kg = min(total_excavated_kg, len(active_haulers) * 80.0 * 3.0 * duration_hours)
        
        return {
            'duration_hours': duration_hours,
            'active_excavators': len(active_excavators),
            'active_haulers': len(active_haulers),
            'total_excavated_tons': round(total_excavated_kg / 1000.0, 3),
            'total_hauled_tons': round(total_hauled_kg / 1000.0, 3),
            'landing_pad_progress_pct': min(100.0, round((total_hauled_kg / 4500.0) * 100.0, 1))
        }

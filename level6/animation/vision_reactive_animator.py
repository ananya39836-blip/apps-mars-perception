"""Computer Vision + Animation Engine — OpenCV & MediaPipe Modality.
Provides reactive feature tracking, Lucas-Kanade optical flow vector fields,
skeletal landmark graph animations, interactive Plotly CV visualizer, and OpenCV/MediaPipe scripts.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class VisionReactiveAnimator:
    """Reactive Computer Vision Animation and Landmark Vector Field Generator."""

    def __init__(self, frame_width: int = 640, frame_height: int = 480, num_frames: int = 30) -> None:
        self.width = frame_width
        self.height = frame_height
        self.num_frames = num_frames

    # -------------------------------------------------------------------------
    # Lucas-Kanade Optical Flow Vector Field Simulation
    # -------------------------------------------------------------------------
    def simulate_reactive_optical_flow(self) -> List[Dict[str, Any]]:
        """Simulate optical flow displacement field responding to a moving object."""
        # 16 grid points across the image
        gx = np.linspace(50, self.width - 50, 10)
        gy = np.linspace(50, self.height - 50, 8)
        xx, yy = np.meshgrid(gx, gy)
        base_x = xx.flatten()
        base_y = yy.flatten()

        frames = []
        for f in range(self.num_frames):
            t = f / self.num_frames
            # Moving obstacle / rover center
            target_cx = self.width * (0.2 + 0.6 * t)
            target_cy = self.height * (0.5 + 0.2 * np.sin(2 * np.pi * t))

            # Optical flow vectors induced by target motion
            dx = base_x - target_cx
            dy = base_y - target_cy
            dist_sq = dx**2 + dy**2 + 1e-4

            # Induced velocity: decays with distance squared
            flow_u = 40.0 * np.exp(-dist_sq / (120.0**2))
            flow_v = 15.0 * np.cos(2 * np.pi * t) * np.exp(-dist_sq / (120.0**2))

            frames.append({
                "frame_idx": f,
                "target_center": (float(target_cx), float(target_cy)),
                "grid_x": base_x.tolist(),
                "grid_y": base_y.tolist(),
                "flow_u": flow_u.tolist(),
                "flow_v": flow_v.tolist(),
                "mean_flow_magnitude": float(np.mean(np.hypot(flow_u, flow_v))),
            })
        return frames

    # -------------------------------------------------------------------------
    # MediaPipe Landmark Skeletal Mesh Simulation
    # -------------------------------------------------------------------------
    def simulate_rover_landmark_skeleton(self) -> List[Dict[str, Any]]:
        """Simulate 12-landmark skeletal wireframe for autonomous rover chassis & rocker-bogie."""
        frames = []
        for f in range(self.num_frames):
            phase = 2 * np.pi * (f / self.num_frames)
            # Chassis center
            cx = self.width / 2 + 60 * np.sin(phase)
            cy = self.height / 2 + 20 * np.cos(2 * phase)

            # 12 landmarks: chassis corners (4), bogie pivots (2), wheels (6)
            landmarks = [
                # Chassis
                [cx - 80, cy - 40],
                [cx + 80, cy - 40],
                [cx + 80, cy + 30],
                [cx - 80, cy + 30],
                # Rocker pivots
                [cx - 40, cy + 20],
                [cx + 40, cy + 20],
                # Wheels
                [cx - 100, cy + 70 + 10 * np.sin(phase)],
                [cx - 60, cy + 75 + 10 * np.cos(phase)],
                [cx - 20, cy + 70 - 10 * np.sin(phase)],
                [cx + 20, cy + 70 + 10 * np.sin(phase + 1)],
                [cx + 60, cy + 75 + 10 * np.cos(phase + 1)],
                [cx + 100, cy + 70 - 10 * np.sin(phase + 1)],
            ]
            frames.append({"frame": f, "landmarks": landmarks})
        return frames

    # -------------------------------------------------------------------------
    # Plotly Animated Vision Reactive Figure Generator
    # -------------------------------------------------------------------------
    def build_plotly_vision_figure(self) -> Dict[str, Any]:
        """Build interactive animated Plotly figure of reactive optical flow & landmarks."""
        flow_frames = self.simulate_reactive_optical_flow()
        skel_frames = self.simulate_rover_landmark_skeleton()

        frames = []
        for i in range(len(flow_frames)):
            ff = flow_frames[i]
            sf = skel_frames[i]
            lm = np.array(sf["landmarks"])

            # Arrow segments for optical flow
            arrow_x, arrow_y = [], []
            for gx, gy, u, v in zip(ff["grid_x"], ff["grid_y"], ff["flow_u"], ff["flow_v"]):
                arrow_x.extend([gx, gx + u, None])
                arrow_y.extend([gy, gy + v, None])

            frames.append({
                "name": f"f_{i}",
                "data": [
                    # Optical flow vector arrows
                    {
                        "type": "scatter",
                        "x": arrow_x,
                        "y": arrow_y,
                        "mode": "lines",
                        "line": {"color": "#00f0ff", "width": 1.5},
                        "name": "Optical Flow Vectors",
                    },
                    # Grid points
                    {
                        "type": "scatter",
                        "x": ff["grid_x"],
                        "y": ff["grid_y"],
                        "mode": "markers",
                        "marker": {"color": "#336699", "size": 3},
                        "name": "Feature Grid",
                    },
                    # Skeletal landmarks
                    {
                        "type": "scatter",
                        "x": lm[:, 0].tolist(),
                        "y": lm[:, 1].tolist(),
                        "mode": "markers+text",
                        "marker": {"color": "#ff007f", "size": 9},
                        "text": [f"L{idx}" for idx in range(12)],
                        "textposition": "top center",
                        "name": "MediaPipe Landmarks",
                    },
                ],
            })

        initial_data = frames[0]["data"]
        layout = {
            "title": "Computer Vision Reactive Optical Flow & Skeletal Landmarks (OpenCV / MediaPipe Modality)",
            "xaxis": {"range": [0, self.width], "title": "Image X (px)", "gridcolor": "#222"},
            "yaxis": {"range": [self.height, 0], "title": "Image Y (px)", "gridcolor": "#222"},  # Inverted image coords
            "template": "plotly_dark",
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Stream Video Tracking",
                            "method": "animate",
                            "args": [None, {"frame": {"duration": 50, "redraw": True}, "fromcurrent": True}],
                        },
                        {
                            "label": "⏸ Pause",
                            "method": "animate",
                            "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                        },
                    ],
                }
            ],
            "sliders": [
                {
                    "steps": [
                        {
                            "args": [[f"f_{k}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                            "label": f"F{k}",
                            "method": "animate",
                        }
                        for k in range(0, len(flow_frames), 2)
                    ],
                    "x": 0.1,
                    "len": 0.9,
                }
            ],
        }
        return {"data": initial_data, "layout": layout, "frames": frames}

    # -------------------------------------------------------------------------
    # Code Generators
    # -------------------------------------------------------------------------
    def generate_opencv_optical_flow_script(self) -> str:
        """Generate a complete standalone OpenCV dense and Lucas-Kanade optical flow script."""
        return '''# Computer Vision Reactive Animation in OpenCV
import cv2
import numpy as np

cap = cv2.VideoCapture(0)  # Or video file path
ret, first_frame = cap.read()
if not ret:
    print("Camera feed not accessible, generating synthetic feed.")
    first_frame = np.zeros((480, 640, 3), dtype=np.uint8)

prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
mask = np.zeros_like(first_frame)

print("Starting OpenCV Lucas-Kanade feature & Farneback flow loop. Press 'q' to quit.")
while True:
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Farneback Optical Flow
    flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    
    # Render reactive motion quiver vectors
    step = 24
    h, w = gray.shape
    y, x = np.mgrid[step//2:h:step, step//2:w:step].reshape(2, -1).astype(int)
    fx, fy = flow[y, x].T
    lines = np.vstack([x, y, x + fx * 3, y + fy * 3]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    
    vis = frame.copy()
    for (x1, y1), (x2, y2) in lines:
        cv2.arrowedLine(vis, (x1, y1), (x2, y2), (0, 255, 255), 1, tipLength=0.3)
    
    cv2.imshow("APPS OpenCV Reactive Optical Flow", vis)
    prev_gray = gray
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
'''

    def generate_mediapipe_script(self) -> str:
        """Generate a complete standalone MediaPipe pose and landmark tracking script."""
        return '''# Computer Vision Animation with Google MediaPipe
import cv2
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0)
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Color conversion
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        
        # Draw skeleton landmarks
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 240, 255), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(255, 0, 128), thickness=2)
            )
        
        cv2.imshow("APPS MediaPipe Reactive Landmark Animation", image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
'''

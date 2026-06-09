import asyncio
from pathlib import Path

import cv2
import numpy as np

from app.models.schemas import VideoMetrics


class VideoAnalyzer:
    """Basic video presence analysis using OpenCV (eye contact, posture, gestures)."""

    SAMPLE_INTERVAL_SECONDS = 2.0
    MAX_FRAMES = 300

    async def analyze(self, video_path: Path) -> VideoMetrics:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, video_path)

    def _analyze_sync(self, video_path: Path) -> VideoMetrics:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return VideoMetrics(notes="Could not open video file for analysis.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_step = max(1, int(fps * self.SAMPLE_INTERVAL_SECONDS))

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        eye_scores: list[float] = []
        posture_scores: list[float] = []
        gesture_scores: list[float] = []
        frames_analyzed = 0
        prev_gray = None

        frame_idx = 0
        while frame_idx < total_frames and frames_analyzed < self.MAX_FRAMES:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = frame.shape[:2]

            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            if len(faces) > 0:
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                face_center_x = fx + fw / 2
                center_offset = abs(face_center_x - w / 2) / (w / 2)
                eye_scores.append(max(0.0, 100.0 - center_offset * 60))

                face_ratio = fh / h
                posture_scores.append(
                    max(0.0, min(100.0, 70 + (face_ratio - 0.25) * 200))
                )
            else:
                eye_scores.append(30.0)
                posture_scores.append(40.0)

            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                motion = float(np.mean(diff))
                gesture_scores.append(min(100.0, motion * 2.5))
            prev_gray = gray

            frames_analyzed += 1
            frame_idx += frame_step

        cap.release()

        if frames_analyzed == 0:
            return VideoMetrics(notes="No frames could be analyzed.")

        return VideoMetrics(
            eye_contact_score=round(float(np.mean(eye_scores)), 1),
            posture_score=round(float(np.mean(posture_scores)), 1),
            gestures_score=round(float(np.mean(gesture_scores)), 1),
            frames_analyzed=frames_analyzed,
            notes="Heuristic analysis based on face detection and motion.",
        )

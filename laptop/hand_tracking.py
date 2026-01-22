# laptop/hand_tracking.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class HandResult:
    # Normalized landmarks: (21, 3) in [0..1] for x/y, z is relative
    landmarks: np.ndarray
    handedness: str
    score: float
    image_bgr: np.ndarray  # annotated frame


class MediaPipeHandTracker:
    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._mp_styles = mp.solutions.drawing_styles

        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=1,
        )

    def process(self, frame_bgr: np.ndarray) -> Optional[HandResult]:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self._hands.process(frame_rgb)

        annotated = frame_bgr.copy()

        if not res.multi_hand_landmarks or not res.multi_handedness:
            return None

        # Choose first hand
        hand_lms = res.multi_hand_landmarks[0]
        handness = res.multi_handedness[0].classification[0].label
        score = float(res.multi_handedness[0].classification[0].score)

        self._mp_draw.draw_landmarks(
            annotated,
            hand_lms,
            self._mp_hands.HAND_CONNECTIONS,
            self._mp_styles.get_default_hand_landmarks_style(),
            self._mp_styles.get_default_hand_connections_style(),
        )

        lms = np.array([[lm.x, lm.y, lm.z] for lm in hand_lms.landmark], dtype=np.float32)

        # HUD
        cv2.putText(
            annotated,
            f"{handness} score={score:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        return HandResult(landmarks=lms, handedness=handness, score=score, image_bgr=annotated)

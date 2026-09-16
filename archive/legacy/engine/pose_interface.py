# archive/legacy/engine/pose_interface.py — Archived legacy pose interface
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time

@dataclass
class PoseResult:
    """Standardized output structure for pose estimation models."""
    track_id: int
    posture: str                  # 'standing', 'sitting', 'crouching', 'fallen', 'unknown'
    confidence: float
    keypoints: List[List[float]]  # [[x, y, conf], ...] 17 COCO keypoints
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PoseEngineInterface(ABC):
    """
    Abstract interface for Pose Estimation backends (e.g., YOLOv8-pose, MediaPipe).
    Ensures modularity so pose estimation can be integrated without modifying the core pipeline.
    """
    @abstractmethod
    def detect_pose(self, frame, person_bbox: List[int], track_id: int = 0) -> Optional[PoseResult]:
        pass

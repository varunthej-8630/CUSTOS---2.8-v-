# services/camera_service.py — High-Level Camera Management Service
from typing import List, Dict, Any, Optional
from engine.health.camera_manager import CameraManager
from engine.health.health_monitor import system_health

class CameraService:
    """Provides high-level business logic and operations for video camera streams."""

    def __init__(self, manager: Optional[CameraManager] = None):
        self._manager = manager

    @property
    def manager(self) -> CameraManager:
        if self._manager is None:
            self._manager = CameraManager()
        return self._manager

    def get_all_cameras(self) -> List[Dict[str, Any]]:
        return self.manager.get_all_camera_stats()

    def get_camera_status(self, camera_id: int) -> Dict[str, Any]:
        return self.manager.get_camera_stats(camera_id)

    def start_cameras(self, sources: List[Any]):
        self.manager.start_cameras(sources)

    def stop_cameras(self):
        self.manager.stop_all()

    def set_camera_zones(self, camera_id: int, zones: list, zone_types: list, is_armed: bool = True):
        self.manager.set_zones(camera_id, zones, zone_types, is_armed)

    def get_system_health(self) -> Dict[str, Any]:
        return system_health.get_status()

camera_service = CameraService()

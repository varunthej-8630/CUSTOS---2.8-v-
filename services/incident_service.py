# services/incident_service.py — High-Level Incident Lifecycle Service
from typing import List, Dict, Any, Optional
from database.database_manager import db_manager
from engine.incidents.incident_lifecycle import incident_lifecycle_mgr

class IncidentService:
    """Provides high-level incident management, querying, and resolution operations."""

    def __init__(self, lifecycle_mgr=None, database_mgr=None):
        self.lifecycle_mgr = lifecycle_mgr or incident_lifecycle_mgr
        self.db = database_mgr or db_manager

    def get_incidents(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.db.get_incidents(limit=limit, offset=offset, status=status)

    def get_incident_by_id(self, incident_id: int) -> Optional[Dict[str, Any]]:
        return self.db.get_incident(incident_id)

    def resolve_incident(self, incident_id: int, resolved_by: str = 'operator', notes: str = '') -> bool:
        return self.db.resolve_incident(incident_id, resolved_by=resolved_by, notes=notes)

    def dismiss_incident(self, incident_id: int, reason: str = 'false_alarm') -> bool:
        return self.db.dismiss_incident(incident_id, reason=reason)

    def get_active_incidents_count(self) -> int:
        return self.db.get_active_incidents_count()

incident_service = IncidentService()

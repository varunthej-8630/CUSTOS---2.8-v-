# services/situation_service.py — High-Level Situation Intelligence Service
from typing import Dict, Any, List, Optional
from engine.situations.situation_engine import situation_engine

class SituationService:
    """Provides high-level situation awareness and cluster intelligence operations."""

    def __init__(self, engine=None):
        self.engine = engine or situation_engine

    def get_current_situations(self) -> List[Dict[str, Any]]:
        return self.engine.get_all_situations()

    def get_situation_by_id(self, situation_id: str) -> Optional[Dict[str, Any]]:
        return self.engine.get_situation(situation_id)

    def get_highest_threat_situation(self) -> Optional[Dict[str, Any]]:
        situations = self.engine.get_all_situations()
        if not situations:
            return None
        return max(situations, key=lambda s: s.get('threat_score', 0.0))

situation_service = SituationService()

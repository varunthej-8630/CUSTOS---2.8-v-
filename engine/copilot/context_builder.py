# engine/copilot/context_builder.py — Copilot Security Context Aggregator
from typing import Dict, Any, List, Optional
import time

class CopilotContextBuilder:
    """
    Aggregates multimodal security signals into a unified situational context:
      - Security Situation state
      - Risk trajectory & breakdown from RiskEngine
      - Subject profile, clusters, and facial identities
      - Zone topology & severity ratings
      - Historical incident & evidence logs
    """

    def build_context(
        self,
        camera_id: int,
        situation: Optional[Dict[str, Any]] = None,
        risk_output: Optional[Dict[str, Any]] = None,
        tracked_subjects: Optional[List[Dict[str, Any]]] = None,
        active_zones: Optional[List[Dict[str, Any]]] = None,
        recent_incidents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return {
            'timestamp': time.time(),
            'camera_id': camera_id,
            'situation': situation or {},
            'risk_output': risk_output or {'total_score': 0.0, 'breakdown': {}},
            'subjects': tracked_subjects or [],
            'zones': active_zones or [],
            'recent_incidents': recent_incidents or [],
        }

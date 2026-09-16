# engine/copilot/recommendation_engine.py — Copilot Action & SOP Recommendation Engine
from typing import Dict, Any, List

class CopilotRecommendationEngine:
    """
    Generates tailored Standard Operating Procedure (SOP) recommendations based on risk dynamics.
    """

    def generate_recommendations(self, decision: Dict[str, Any]) -> List[str]:
        risk_level = decision.get('current_risk', {}).get('level', 'LOW')
        if risk_level in ('CRITICAL', 'HIGH'):
            return [
                "1. Immediately alert on-duty security patrol.",
                "2. Lock down monitored high-security egress doors.",
                "3. Preserve full-resolution pre-event video clip and tamper logs."
            ]
        elif risk_level == 'MEDIUM':
            return [
                "1. Direct PTZ or nearest camera toward monitored subject.",
                "2. Monitor subject dwell time for potential loitering escalation."
            ]
        return [
            "1. Routine perimeter scan active. No immediate intervention required."
        ]

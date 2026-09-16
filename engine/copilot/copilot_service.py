# engine/copilot/copilot_service.py — Unified Copilot Facade Service
from typing import Dict, Any, Optional
from engine.copilot.context_builder import CopilotContextBuilder
from engine.copilot.decision_engine import SecurityDecisionEngine
from engine.copilot.recommendation_engine import CopilotRecommendationEngine

class CopilotService:
    """Unified facade coordinating context building, decision generation, and recommendations."""

    def __init__(self):
        self.context_builder = CopilotContextBuilder()
        self.decision_engine = SecurityDecisionEngine()
        self.recommendation_engine = CopilotRecommendationEngine()

    def analyze_situation(
        self,
        camera_id: int = 0,
        situation: Optional[Dict[str, Any]] = None,
        risk_output: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = self.context_builder.build_context(
            camera_id=camera_id,
            situation=situation,
            risk_output=risk_output,
        )
        decision = self.decision_engine.evaluate(context)
        recommendations = self.recommendation_engine.generate_recommendations(decision)
        decision['recommendations'] = recommendations
        return decision

copilot_service = CopilotService()

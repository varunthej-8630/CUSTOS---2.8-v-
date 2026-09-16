# engine/copilot/decision_engine.py — Copilot Structured Security Decision Engine
from typing import Dict, Any, List

class SecurityDecisionEngine:
    """
    Synthesizes security context into deterministic, operator-ready decision artifacts:
      - WHAT IS HAPPENING?
      - WHAT IS THE CURRENT RISK?
      - WHAT CHANGED?
      - WHAT SHOULD THE OPERATOR VERIFY?
      - WHAT ACTIONS ARE AVAILABLE?
      - WHAT WOULD HAPPEN IF NOTHING IS DONE?
      - WHAT EVIDENCE SUPPORTS THIS?
    """

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        situation = context.get('situation', {})
        risk = context.get('risk_output', {})
        score = risk.get('total_score', situation.get('threat_score', 0.0))
        
        # Structure decision
        what_happening = situation.get('summary', 'Normal perimeter surveillance active.')
        current_risk_level = 'CRITICAL' if score >= 80 else 'HIGH' if score >= 60 else 'MEDIUM' if score >= 35 else 'LOW'
        
        return {
            'what_is_happening': what_happening,
            'current_risk': {
                'score': score,
                'level': current_risk_level,
                'breakdown': risk.get('breakdown', {})
            },
            'what_changed': situation.get('recent_changes', ['No significant state changes']),
            'operator_verification': [
                'Verify subject authorization in zone',
                'Inspect live camera feed for physical security breaches',
            ],
            'available_actions': [
                {'action': 'ACKNOWLEDGE', 'label': 'Acknowledge Event'},
                {'action': 'DISPATCH', 'label': 'Dispatch Security Guard'},
                {'action': 'DISMISS', 'label': 'Mark False Alarm'},
            ],
            'inaction_consequence': 'Risk of unmonitored escalation if zone perimeter is breached.',
            'supporting_evidence': situation.get('evidence_ids', []),
        }

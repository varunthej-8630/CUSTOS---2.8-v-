# services/notification_service.py — High-Level Alert Notification Service
from typing import Dict, Any, Optional
from core.logging import alert_logger

class NotificationService:
    """Dispatches alerts to audio alarms, desktop popups, Telegram bots, and WebSockets."""

    def __init__(self, alert_manager=None):
        self.alert_manager = alert_manager

    def set_alert_manager(self, alert_manager):
        self.alert_manager = alert_manager

    def notify_incident(self, incident_data: Dict[str, Any]):
        alert_logger.info(f"[NOTIFICATION] Incident Alert: {incident_data.get('id', 'N/A')} - {incident_data.get('zone_name', 'Zone')}")
        if self.alert_manager and hasattr(self.alert_manager, 'send_alert'):
            self.alert_manager.send_alert(incident_data)

notification_service = NotificationService()

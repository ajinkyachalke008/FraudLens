"""
Alert Broadcaster — Delivers alerts via WebSocket (Redis PubSub).
"""
import logging
from models.sql.fraud_alert import FraudAlert
from services.alerts.alert_rules import ALERT_TEMPLATES

logger = logging.getLogger(__name__)


async def broadcast_alert(alert: FraudAlert, escalation: bool = False) -> None:
    """
    Format and broadcast an alert via Redis PubSub → WebSocket.
    The websockets.py redis_listener picks this up and pushes to all connected clients.
    """
    template = ALERT_TEMPLATES.get(alert.alert_type, {})
    requires_ack = template.get("requires_ack", alert.severity in ("EMERGENCY", "CRITICAL", "HIGH"))

    message = {
        "type": "FRAUD_ALERT",
        "data": {
            "alert_id": str(alert.id),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "account_id": alert.account_id,
            "case_id": str(alert.case_id) if alert.case_id else None,
            "requires_ack": requires_ack,
            "escalation_level": alert.escalation_level if escalation else 0,
            "trigger_data": alert.trigger_data or {},
            "icon": template.get("icon", "🔔"),
            "color": template.get("color", "blue"),
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
    }

    try:
        from core.pubsub import publish_alert
        await publish_alert("fraud_alerts", message)
        logger.info(
            f"Alert broadcast: [{alert.severity}] {alert.alert_type} — {alert.title}"
            + (f" (escalation L{alert.escalation_level})" if escalation else "")
        )
    except Exception as e:
        # Broadcast failure should never block alert creation
        logger.error(f"Alert broadcast failed (alert still created): {e}")

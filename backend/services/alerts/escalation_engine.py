"""
Escalation Engine — Background task that checks for unacknowledged alerts
and escalates them according to the escalation ladder.

Registered as asyncio.create_task() in main.py lifespan.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.sql.fraud_alert import FraudAlert
from services.alerts.alert_broadcaster import broadcast_alert
from services.alerts.alert_rules import ESCALATION_LADDER

logger = logging.getLogger(__name__)

# Check interval (seconds)
CHECK_INTERVAL = 60


async def run_escalation_checks(ctx: dict):
    """
    Runs as an arq cron job.
    Checks for unacknowledged alerts past their escalation windows.

    Escalation levels:
      Level 0 → Level 1: Re-broadcast with pulse animation
      Level 1 → Level 2: Notify supervisor (if assigned_to exists)
      Level 2 → Level 3: Force CRITICAL severity, broadcast to ALL connections
    """
    logger.info("Escalation engine running Arq cron job")
    
    try:
        async with AsyncSessionLocal() as db:
            await _process_escalations(db)
            await db.commit()
    except Exception as e:
        logger.error(f"Escalation check error: {e}")


async def _process_escalations(db: AsyncSession):
    """Process all pending escalations."""
    now = datetime.utcnow()

    # ── Level 0 → Level 1: Re-notify ──────────────────────────
    for severity, minutes in ESCALATION_LADDER.items():
        if minutes is None or minutes == 0:
            continue  # No escalation or instant (already handled)

        cutoff = now - timedelta(minutes=minutes)

        result = await db.execute(
            select(FraudAlert).where(
                FraudAlert.acknowledged == False,
                FraudAlert.severity == severity,
                FraudAlert.escalation_level == 0,
                FraudAlert.created_at < cutoff,
                FraudAlert.status == "active",
            )
        )
        alerts = result.scalars().all()

        for alert in alerts:
            alert.escalation_level = 1
            alert.escalated_at = now
            logger.warning(
                f"Escalation L1: [{alert.severity}] {alert.title} "
                f"— unacked for {minutes}+ min"
            )
            try:
                await broadcast_alert(alert, escalation=True)
            except Exception as e:
                logger.error(f"L1 escalation broadcast failed: {e}")

    # ── Level 1 → Level 2: Supervisor notify (30 min after L1) ─
    l2_cutoff = now - timedelta(minutes=30)
    result = await db.execute(
        select(FraudAlert).where(
            FraudAlert.acknowledged == False,
            FraudAlert.escalation_level == 1,
            FraudAlert.escalated_at < l2_cutoff,
            FraudAlert.severity.in_(["CRITICAL", "HIGH"]),
            FraudAlert.status == "active",
        )
    )
    for alert in result.scalars():
        alert.escalation_level = 2
        alert.escalated_at = now
        logger.warning(
            f"Escalation L2 (supervisor): [{alert.severity}] {alert.title} "
            f"— unacked for 30+ min after L1"
        )
        try:
            await broadcast_alert(alert, escalation=True)
        except Exception as e:
            logger.error(f"L2 escalation broadcast failed: {e}")

    # ── Level 2 → Level 3: Force CRITICAL + broadcast to ALL ──
    l3_cutoff = now - timedelta(minutes=60)
    result = await db.execute(
        select(FraudAlert).where(
            FraudAlert.acknowledged == False,
            FraudAlert.escalation_level == 2,
            FraudAlert.escalated_at < l3_cutoff,
            FraudAlert.status == "active",
        )
    )
    for alert in result.scalars():
        alert.escalation_level = 3
        alert.severity = "CRITICAL"  # Force upgrade
        alert.escalated_at = now
        logger.critical(
            f"Escalation L3 (BROADCAST ALL): {alert.title} "
            f"— unacked for 60+ min, forced CRITICAL"
        )
        try:
            await broadcast_alert(alert, escalation=True)
        except Exception as e:
            logger.error(f"L3 escalation broadcast failed: {e}")

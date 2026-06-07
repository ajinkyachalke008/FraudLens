"""
Alert Engine — Central alert creation, routing, and auto-assignment.
This is the single entry point for creating alerts from any source.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.sql.fraud_alert import FraudAlert
from models.sql.case import Case
from services.alerts.alert_suppressor import should_suppress, _make_suppression_key
from services.alerts.alert_broadcaster import broadcast_alert

logger = logging.getLogger(__name__)


async def create_alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    account_id: Optional[str] = None,
    case_id: Optional[str] = None,
    trigger_data: dict = {},
    transaction_ids: list = [],
    db: Optional[AsyncSession] = None,
) -> Optional[FraudAlert]:
    """
    Central alert creation.

    Flow:
    1. Check suppression (dedup)
    2. Create FraudAlert record
    3. Auto-assign to case investigator if case_id provided
    4. Broadcast via WebSocket
    5. Return created alert (or None if suppressed)
    """
    # Step 1: Suppression check
    if await should_suppress(alert_type, account_id, db):
        logger.debug(f"Alert suppressed: {alert_type} for {account_id}")
        return None

    # Step 2: Create alert
    alert = FraudAlert(
        id=uuid.uuid4(),
        alert_type=alert_type,
        severity=severity,
        title=title[:200],
        message=message,
        account_id=account_id,
        case_id=uuid.UUID(case_id) if case_id else None,
        trigger_data=trigger_data,
        transaction_ids=transaction_ids or [],
        status="active",
        acknowledged=False,
        escalation_level=0,
        suppression_key=_make_suppression_key(alert_type, account_id),
        created_at=datetime.utcnow(),
    )

    # Step 3: Auto-assign to case investigator
    if case_id and db:
        try:
            case_result = await db.execute(
                select(Case.assigned_to).where(Case.id == uuid.UUID(case_id))
            )
            assigned_to = case_result.scalar_one_or_none()
            if assigned_to:
                alert.assigned_to = assigned_to
                logger.info(f"Alert auto-assigned to investigator {assigned_to}")
        except Exception as e:
            logger.warning(f"Auto-assign failed (alert still created): {e}")

    # Step 4: Persist to DB
    if db:
        try:
            db.add(alert)
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to persist alert: {e}")
            # Still broadcast even if DB fails
            alert.created_at = datetime.utcnow()

    # Step 5: Broadcast via WebSocket
    try:
        await broadcast_alert(alert)
    except Exception as e:
        logger.error(f"Alert broadcast failed: {e}")

    logger.info(
        f"Alert created: [{severity}] {alert_type} — {title}"
        + (f" → assigned to case {case_id}" if case_id else "")
    )

    return alert


async def acknowledge_alert(
    alert_id: str,
    user_id: str,
    db: AsyncSession,
) -> Optional[FraudAlert]:
    """Mark an alert as acknowledged."""
    try:
        result = await db.execute(
            select(FraudAlert).where(FraudAlert.id == uuid.UUID(alert_id))
        )
        alert = result.scalar_one_or_none()
        if not alert:
            return None

        alert.acknowledged = True
        alert.acknowledged_by = uuid.UUID(user_id)
        alert.acknowledged_at = datetime.utcnow()
        alert.status = "acknowledged"
        await db.flush()

        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        return alert

    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        return None


async def update_alert_status(
    alert_id: str,
    status: str,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = None,
) -> Optional[FraudAlert]:
    """Update alert status: investigating | resolved | dismissed."""
    try:
        result = await db.execute(
            select(FraudAlert).where(FraudAlert.id == uuid.UUID(alert_id))
        )
        alert = result.scalar_one_or_none()
        if not alert:
            return None

        alert.status = status
        if status == "resolved":
            alert.resolved_at = datetime.utcnow()
        if resolution_notes:
            alert.resolution_notes = resolution_notes
        await db.flush()

        return alert

    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}")
        return None

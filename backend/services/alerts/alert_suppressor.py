"""
Alert Suppressor — Deduplication and cooldown logic.
Prevents alert storms by tracking suppression keys.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.sql.fraud_alert import FraudAlert

logger = logging.getLogger(__name__)


# ──── Cooldown Configuration ─────────────────────────────────
# Minutes to wait before re-alerting same (type + account) combo

COOLDOWN_MINUTES = {
    "RISK_THRESHOLD": 30,       # Don't re-alert same account within 30 min
    "PATTERN_DETECTED": 60,     # Same pattern type, same accounts, 60 min
    "BLACKLIST_HIT": 0,         # NEVER suppress blacklist hits
    "SHARED_ENTITY": 120,       # 2 hour cooldown
    "WATCHLIST_ACTIVITY": 60,   # 1 hour cooldown
    "VELOCITY_SPIKE": 15,       # 15 min cooldown
    "SYNDICATE_JOIN": 0,        # NEVER suppress syndicate alerts
    "INGESTION_ANOMALY": 30,    # 30 min cooldown
}


def _make_suppression_key(alert_type: str, account_id: str = None) -> str:
    """Generate a suppression key for dedup checking."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    account_part = account_id or "GLOBAL"
    return f"{alert_type}:{account_part}:{date_str}"


async def should_suppress(
    alert_type: str,
    account_id: str = None,
    db: AsyncSession = None,
) -> bool:
    """
    Check if a similar alert was created recently within the cooldown window.
    Returns True if the alert should be suppressed (not created).
    """
    cooldown = COOLDOWN_MINUTES.get(alert_type, 30)

    # Cooldown of 0 means never suppress
    if cooldown == 0:
        return False

    if db is None:
        return False

    try:
        cutoff = datetime.utcnow() - timedelta(minutes=cooldown)

        # Check for recent alert with same type + account
        query = select(func.count(FraudAlert.id)).where(
            FraudAlert.alert_type == alert_type,
            FraudAlert.created_at >= cutoff,
        )

        if account_id:
            query = query.where(FraudAlert.account_id == account_id)

        result = await db.execute(query)
        recent_count = result.scalar() or 0

        if recent_count > 0:
            logger.debug(
                f"Suppressing {alert_type} for {account_id}: "
                f"{recent_count} recent alerts within {cooldown}min cooldown"
            )
            return True

        return False

    except Exception as e:
        logger.warning(f"Suppression check failed (allowing alert): {e}")
        return False  # On error, don't suppress — let the alert through

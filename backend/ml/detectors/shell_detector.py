"""
Shell Detector — Detects pass-through / shell account patterns.
Flags: outflow/inflow ratio >0.92 within 24hrs AND avg holding time <2hrs.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ShellDetector:
    PASSTHROUGH_RATIO_THRESHOLD = 0.92
    MAX_HOLDING_HOURS = 2

    def __init__(self):
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        from models.sql.transaction import Transaction

        try:
            now = datetime.utcnow()
            day_ago = now - timedelta(hours=24)

            # Total inflow (received)
            inflow_result = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.to_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            total_inflow = float(inflow_result.scalar() or 0)

            # Total outflow (sent)
            outflow_result = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.from_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            total_outflow = float(outflow_result.scalar() or 0)

            if total_inflow == 0:
                self._evidence = {
                    "inflow_24h": 0, "outflow_24h": total_outflow,
                    "passthrough_ratio": 0, "triggered": False
                }
                return 0.0

            passthrough_ratio = total_outflow / total_inflow

            # Calculate average holding time
            # (avg time between receiving and sending — simplified)
            last_received = await db.execute(
                select(func.max(Transaction.timestamp)).where(
                    Transaction.to_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            last_in_time = last_received.scalar()

            last_sent = await db.execute(
                select(func.min(Transaction.timestamp)).where(
                    Transaction.from_account == account_id,
                    Transaction.timestamp >= day_ago
                )
            )
            first_out_time = last_sent.scalar()

            avg_holding_hours = 24.0  # default safe
            if last_in_time and first_out_time and first_out_time > last_in_time:
                avg_holding_hours = (first_out_time - last_in_time).total_seconds() / 3600

            # Score
            ratio_score = min(passthrough_ratio / self.PASSTHROUGH_RATIO_THRESHOLD, 1.0) if passthrough_ratio > 0.5 else 0.0
            holding_score = max(0, 1.0 - (avg_holding_hours / (self.MAX_HOLDING_HOURS * 3)))
            final = (ratio_score * 0.7 + holding_score * 0.3)

            self._evidence = {
                "inflow_24h": round(total_inflow, 2),
                "outflow_24h": round(total_outflow, 2),
                "passthrough_ratio": round(passthrough_ratio, 3),
                "avg_holding_hours": round(avg_holding_hours, 1),
                "triggered": final > 0.5
            }
            return round(min(final, 1.0), 3)

        except Exception as e:
            logger.warning(f"ShellDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    def get_evidence(self) -> dict:
        return self._evidence

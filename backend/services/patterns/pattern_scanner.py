"""
Pattern Scanner — Orchestrator that runs all 19 detectors in parallel.
Auto-triggers alerts for HIGH/CRITICAL patterns.
"""
import uuid
import asyncio
import logging
import time
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.schemas.patterns import FraudPattern, PatternScanResponse
from models.sql.pattern import DetectedPattern

logger = logging.getLogger(__name__)


def _load_all_detectors():
    """Load all 19 pattern detectors."""
    from services.patterns.smurfing_detector import SmurfingDetector
    from services.patterns.rapid_layering_detector import RapidLayeringDetector
    from services.patterns.round_robin_detector import RoundRobinDetector
    from services.patterns.mule_chain_detector import MuleChainDetector
    from services.patterns.time_cluster_detector import TimeClusterDetector
    from services.patterns.amount_mirror_detector import AmountMirrorDetector
    from services.patterns.even_split_detector import EvenSplitDetector
    from services.patterns.cashout_burst_detector import CashoutBurstDetector
    from services.patterns.reverse_funnel_detector import ReverseFunnelDetector
    from services.patterns.weekend_rush_detector import WeekendRushDetector
    from services.patterns.dormant_activation_detector import DormantActivationDetector
    from services.patterns.crossbank_hop_detector import CrossbankHopDetector
    from ml.patterns.investment_scam import InvestmentScamDetector
    from ml.patterns.otp_fraud import OTPFraudDetector
    from ml.patterns.job_scam import JobScamDetector
    from ml.patterns.romance_scam import RomanceScamDetector
    from ml.patterns.kyc_fraud import KYCFraudDetector
    from ml.patterns.cash_out_pattern import CashOutPatternDetector
    from ml.patterns.layering_detector import LayeringDetector

    return [
        SmurfingDetector(),
        RapidLayeringDetector(),
        RoundRobinDetector(),
        MuleChainDetector(),
        TimeClusterDetector(),
        AmountMirrorDetector(),
        EvenSplitDetector(),
        CashoutBurstDetector(),
        ReverseFunnelDetector(),
        WeekendRushDetector(),
        DormantActivationDetector(),
        CrossbankHopDetector(),
        InvestmentScamDetector(),
        OTPFraudDetector(),
        JobScamDetector(),
        RomanceScamDetector(),
        KYCFraudDetector(),
        CashOutPatternDetector(),
        LayeringDetector(),
    ]


async def _safe_detect(detector, account_ids, db, neo4j_driver, time_range):
    """Run a single detector with error isolation."""
    try:
        return await detector.detect(account_ids, db, neo4j_driver, time_range)
    except Exception as e:
        logger.error(f"Detector {detector.pattern_type} crashed: {e}")
        return []


async def scan_for_patterns(
    account_ids: List[str],
    db: AsyncSession,
    neo4j_driver=None,
    case_id: Optional[str] = None,
    time_range: Optional[Tuple[datetime, datetime]] = None,
    pattern_types: Optional[List[str]] = None,
) -> PatternScanResponse:
    """
    Run all 19 pattern detectors in parallel (fault-tolerant).
    1. Load detectors (optionally filter by pattern_types)
    2. Run all via asyncio.gather
    3. Persist results to detected_patterns table
    4. Auto-generate alerts for HIGH/CRITICAL patterns
    5. Return aggregated response
    """
    start_time = time.time()
    job_id = str(uuid.uuid4())[:8]

    logger.info(
        f"Pattern scan started [job={job_id}]: "
        f"{len(account_ids)} accounts, case={case_id}"
    )

    # Load and filter detectors
    all_detectors = _load_all_detectors()
    if pattern_types:
        all_detectors = [d for d in all_detectors if d.pattern_type in pattern_types]

    # Run all detectors in parallel
    tasks = [
        _safe_detect(d, account_ids, db, neo4j_driver, time_range)
        for d in all_detectors
    ]
    results = await asyncio.gather(*tasks)

    # Flatten results
    all_patterns: List[FraudPattern] = []
    for result_list in results:
        all_patterns.extend(result_list)

    # Persist to DB
    alerts_generated = 0
    for pattern in all_patterns:
        try:
            db_pattern = DetectedPattern(
                id=uuid.UUID(pattern.pattern_id) if len(pattern.pattern_id) == 36 else uuid.uuid4(),
                pattern_type=pattern.pattern_type,
                severity=pattern.severity,
                confidence=pattern.confidence,
                accounts_involved=pattern.involved_accounts,
                transactions_involved=pattern.involved_transactions,
                total_value=pattern.total_amount,
                victim_count=pattern.victim_count,
                time_span_hours=(pattern.timeline_end - pattern.timeline_start).total_seconds() / 3600 if pattern.timeline_start and pattern.timeline_end else None,
                timeline_start=pattern.timeline_start,
                timeline_end=pattern.timeline_end,
                description=pattern.description,
                evidence=pattern.evidence,
                case_id=uuid.UUID(case_id) if case_id else None,
                detected_by="system",
                status="new",
            )
            db.add(db_pattern)
        except Exception as e:
            logger.warning(f"Failed to persist pattern {pattern.pattern_type}: {e}")

        # Auto-generate alerts for HIGH/CRITICAL
        if pattern.severity in ("HIGH", "CRITICAL"):
            try:
                from services.alerts.alert_engine import create_alert
                alert = await create_alert(
                    alert_type="PATTERN_DETECTED",
                    severity=pattern.severity,
                    title=f"{pattern.pattern_icon} {pattern.pattern_type}: {len(pattern.involved_accounts)} accounts, ₹{pattern.total_amount:,.0f}",
                    message=pattern.description,
                    account_id=pattern.involved_accounts[0] if pattern.involved_accounts else None,
                    case_id=case_id,
                    trigger_data={
                        "pattern_id": pattern.pattern_id,
                        "pattern_type": pattern.pattern_type,
                        "confidence": pattern.confidence,
                    },
                    db=db,
                )
                if alert:
                    alerts_generated += 1
                    db_pattern.alert_id = alert.id
            except Exception as e:
                logger.warning(f"Failed to create alert for pattern {pattern.pattern_type}: {e}")

    try:
        await db.flush()
    except Exception as e:
        logger.warning(f"Failed to flush patterns: {e}")

    # Aggregate stats
    by_type = {}
    by_severity = {}
    for p in all_patterns:
        by_type[p.pattern_type] = by_type.get(p.pattern_type, 0) + 1
        by_severity[p.severity] = by_severity.get(p.severity, 0) + 1

    elapsed_ms = int((time.time() - start_time) * 1000)

    logger.info(
        f"Pattern scan complete [job={job_id}]: "
        f"{len(all_patterns)} patterns found, {alerts_generated} alerts, {elapsed_ms}ms"
    )

    return PatternScanResponse(
        job_id=job_id,
        patterns_found=len(all_patterns),
        patterns=all_patterns,
        by_type=by_type,
        by_severity=by_severity,
        scan_duration_ms=elapsed_ms,
        alerts_generated=alerts_generated,
    )

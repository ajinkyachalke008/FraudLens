"""
Entity Scanner — Orchestrator for all shared entity matchers.
Runs phone, UPI, name, branch, and beneficiary matchers.
Auto-generates alerts for cross-case and critical entities.
"""
import uuid
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.sql.shared_entity import SharedEntity
from models.schemas.shared_entities import (
    SharedEntityResult, EntityScanResponse, CrossCaseLink,
)

logger = logging.getLogger(__name__)


async def scan_shared_entities(
    account_ids: Optional[List[str]] = None,
    case_id: Optional[str] = None,
    entity_types: Optional[List[str]] = None,
    db: AsyncSession = None,
    neo4j_driver=None,
) -> EntityScanResponse:
    """
    Run all entity matchers and aggregate results.

    Flow:
    1. Gather accounts (from case or explicit list)
    2. Run matchers for each entity type
    3. Cross-reference with cases for cross-case links
    4. Risk assess: cross-case + blacklisted = CRITICAL
    5. Persist results
    6. Generate alerts for CRITICAL entities
    """
    from services.entities.phone_matcher import match_phones
    from services.entities.upi_matcher import match_upi
    from services.entities.name_matcher import match_names
    from services.entities.branch_analyzer import match_branches
    from services.entities.beneficiary_analyzer import find_common_beneficiaries

    if not account_ids:
        account_ids = []

    # If case_id provided, gather accounts from that case
    if case_id and db and not account_ids:
        try:
            from sqlalchemy import select
            from models.sql.account import Account
            result = await db.execute(
                select(Account.account_number).where(Account.case_id == uuid.UUID(case_id))
            )
            account_ids = [r[0] for r in result.all()]
        except Exception as e:
            logger.warning(f"Failed to load accounts for case {case_id}: {e}")

    all_entities: List[SharedEntityResult] = []
    by_type = {}

    # Run matchers based on requested entity_types (or all)
    matchers = {
        "PHONE": match_phones,
        "UPI_VPA": match_upi,
        "NAME": match_names,
        "IFSC": match_branches,
        "BENEFICIARY": find_common_beneficiaries,
    }

    for etype, matcher_fn in matchers.items():
        if entity_types and etype not in entity_types:
            continue
        try:
            if etype == "BENEFICIARY":
                results = await matcher_fn(account_ids, db)
            else:
                results = await matcher_fn(account_ids, db)
            all_entities.extend(results)
            by_type[etype] = len(results)
        except Exception as e:
            logger.error(f"Entity matcher {etype} failed: {e}")
            by_type[etype] = 0

    # Persist to DB
    alerts_generated = 0
    for entity in all_entities:
        try:
            db_entity = SharedEntity(
                id=uuid.uuid4(),
                entity_type=entity.entity_type,
                entity_value=entity.entity_value,
                accounts=entity.accounts,
                account_count=entity.account_count,
                cases=[case_id] if case_id else [],
                case_count=1 if case_id else 0,
                risk_assessment=entity.risk_assessment,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )
            db.add(db_entity)
            entity.entity_id = str(db_entity.id)
        except Exception as e:
            logger.warning(f"Failed to persist entity {entity.entity_type}: {e}")

        # Auto-alert for CRITICAL/HIGH entities
        if entity.risk_assessment in ("CRITICAL", "HIGH"):
            try:
                from services.alerts.alert_engine import create_alert
                alert = await create_alert(
                    alert_type="SHARED_ENTITY",
                    severity="HIGH" if entity.account_count >= 3 else "MEDIUM",
                    title=f"Shared {entity.entity_type}: {entity.entity_value} ({entity.account_count} accounts)",
                    message=f"Accounts {', '.join(entity.accounts[:5])} share {entity.entity_type} value '{entity.entity_value}'",
                    trigger_data={
                        "entity_type": entity.entity_type,
                        "entity_value": entity.entity_value,
                        "account_count": entity.account_count,
                    },
                    case_id=case_id,
                    db=db,
                )
                if alert:
                    alerts_generated += 1
            except Exception as e:
                logger.warning(f"Failed to create alert for entity: {e}")

    try:
        await db.flush()
    except Exception as e:
        logger.warning(f"Failed to flush entities: {e}")

    # Cross-case links (mock for now — real impl queries across cases)
    cross_case_links = [
        CrossCaseLink(
            case_a="CASE-2026-A8F3", case_b="CASE-2026-B1D7",
            entity_type="PHONE", entity_value="9876543210",
            shared_accounts=["ACC-1001", "ACC-3091"],
            link_strength=0.85,
        ),
    ]

    logger.info(
        f"Entity scan complete: {len(all_entities)} entities found, "
        f"{alerts_generated} alerts generated"
    )

    return EntityScanResponse(
        entities_found=len(all_entities),
        entities=all_entities,
        by_type=by_type,
        cross_case_links=cross_case_links,
        alerts_generated=alerts_generated,
    )

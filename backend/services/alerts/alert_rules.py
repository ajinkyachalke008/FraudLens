"""
Alert Rules — Configurable trigger rules with severity mappings and templates.
"""
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class AlertRule:
    """Defines a single alert trigger rule."""
    name: str
    alert_type: str
    severity: str
    template: str
    description: str = ""


# ──── Risk Score Thresholds ───────────────────────────────────

RISK_THRESHOLD_RULES = {
    "CRITICAL": {
        "min_score": 0.75,
        "severity": "CRITICAL",
        "template": "Account {account_id} risk score crossed CRITICAL ({score:.0%}) — {signals_active}/15 signals active",
    },
    "ALERT": {
        "min_score": 0.50,
        "severity": "HIGH",
        "template": "Account {account_id} risk score elevated to ALERT ({score:.0%})",
    },
    "WATCH": {
        "min_score": 0.30,
        "severity": "MEDIUM",
        "template": "Account {account_id} entered WATCH tier ({score:.0%})",
    },
}


# ──── Pattern Severity Mapping ────────────────────────────────

PATTERN_SEVERITY_MAP = {
    "CRITICAL": "CRITICAL",
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
}


# ──── Named Alert Rules ──────────────────────────────────────

ALERT_RULES = [
    AlertRule(
        name="HIGH_RISK_SCORE",
        alert_type="RISK_THRESHOLD",
        severity="CRITICAL",
        template="Account {account_id} risk score crossed CRITICAL ({score:.0%})",
        description="Risk score exceeded 0.75 threshold",
    ),
    AlertRule(
        name="BLACKLIST_TOUCH",
        alert_type="BLACKLIST_HIT",
        severity="EMERGENCY",
        template="Transaction to BLACKLISTED account {account_id} detected — ₹{amount:,.0f}",
        description="Transaction involving a blacklisted account",
    ),
    AlertRule(
        name="VELOCITY_SPIKE",
        alert_type="VELOCITY_SPIKE",
        severity="HIGH",
        template="Velocity spike on {account_id}: {txn_count} txns in 1 hour",
        description="Velocity score exceeded 0.9",
    ),
    AlertRule(
        name="SYNDICATE_JOIN",
        alert_type="SYNDICATE_JOIN",
        severity="CRITICAL",
        template="New account {account_id} linked to syndicate {syndicate_id}",
        description="Account joined a known fraud syndicate cluster",
    ),
    AlertRule(
        name="PATTERN_DETECTED",
        alert_type="PATTERN_DETECTED",
        severity="HIGH",
        template="{pattern_icon} {pattern_type} detected: {account_count} accounts, ₹{total_amount:,.0f}",
        description="Fraud pattern detected by pattern scanner",
    ),
    AlertRule(
        name="SHARED_ENTITY_CROSS_CASE",
        alert_type="SHARED_ENTITY",
        severity="HIGH",
        template="Shared {entity_type}: {entity_value} found across {case_count} cases",
        description="Same entity found in multiple cases",
    ),
    AlertRule(
        name="WATCHLIST_ACTIVITY",
        alert_type="WATCHLIST_ACTIVITY",
        severity="MEDIUM",
        template="Watchlist account {account_id} active — new transaction detected",
        description="Watchlisted account has new activity",
    ),
]


# ──── Escalation Ladder ──────────────────────────────────────

ESCALATION_LADDER = {
    "EMERGENCY": 0,      # Instant → all channels, full-screen modal
    "CRITICAL": 10,      # 10 min → Level 1 re-notify + pulse
    "HIGH": 30,          # 30 min → Level 2 supervisor
    "MEDIUM": 240,       # 4 hours → Level 1 re-notify
    "LOW": None,         # No escalation
}


# ──── Alert Templates ────────────────────────────────────────

ALERT_TEMPLATES = {
    "RISK_THRESHOLD": {
        "icon": "🔴",
        "color": "red",
        "requires_ack": True,
    },
    "PATTERN_DETECTED": {
        "icon": "🔍",
        "color": "orange",
        "requires_ack": True,
    },
    "BLACKLIST_HIT": {
        "icon": "⛔",
        "color": "red",
        "requires_ack": True,
    },
    "SHARED_ENTITY": {
        "icon": "🔗",
        "color": "yellow",
        "requires_ack": False,
    },
    "WATCHLIST_ACTIVITY": {
        "icon": "👁",
        "color": "yellow",
        "requires_ack": False,
    },
    "VELOCITY_SPIKE": {
        "icon": "⚡",
        "color": "orange",
        "requires_ack": True,
    },
    "SYNDICATE_JOIN": {
        "icon": "🕸",
        "color": "red",
        "requires_ack": True,
    },
    "INGESTION_ANOMALY": {
        "icon": "📥",
        "color": "blue",
        "requires_ack": False,
    },
}

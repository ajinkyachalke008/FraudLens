"""
Pattern Registry — Defines all 19 pattern types with metadata.
Used by the scanner and frontend /types endpoint.
"""

PATTERN_REGISTRY = {
    # ──── Structural Patterns (12) ────────────────────────────
    "SMURFING": {
        "name": "Smurfing", "icon": "💸", "category": "structural",
        "description": "Multiple sub-₹50k transactions aggregating to large sums",
        "severity_default": "HIGH", "engine": "sql",
    },
    "RAPID_LAYERING": {
        "name": "Rapid Layering", "icon": "⚡", "category": "structural",
        "description": "Money bouncing through 3+ accounts in under 1 hour",
        "severity_default": "HIGH", "engine": "neo4j",
    },
    "ROUND_ROBIN": {
        "name": "Round-Robin", "icon": "🔄", "category": "structural",
        "description": "Circular money flow: A→B→C→A",
        "severity_default": "CRITICAL", "engine": "neo4j",
    },
    "MULE_CHAIN": {
        "name": "Mule Chain", "icon": "⛓️", "category": "structural",
        "description": "Linear mule payout chain: A→B→C→D→E",
        "severity_default": "CRITICAL", "engine": "neo4j",
    },
    "TIME_CLUSTER": {
        "name": "Time Cluster", "icon": "⏱️", "category": "structural",
        "description": "10+ transactions clustered within 15-minute window",
        "severity_default": "HIGH", "engine": "sql",
    },
    "AMOUNT_MIRROR": {
        "name": "Amount Mirror", "icon": "🪞", "category": "structural",
        "description": "Pass-through relay: incoming ≈ outgoing within 24h",
        "severity_default": "HIGH", "engine": "sql",
    },
    "EVEN_SPLIT": {
        "name": "Even Split", "icon": "✂️", "category": "structural",
        "description": "One large inflow split into N equal outflows",
        "severity_default": "HIGH", "engine": "sql",
    },
    "CASHOUT_BURST": {
        "name": "Cash-Out Burst", "icon": "🏧", "category": "structural",
        "description": "ATM withdrawal spikes after digital inflows",
        "severity_default": "HIGH", "engine": "sql",
    },
    "REVERSE_FUNNEL": {
        "name": "Reverse Funnel", "icon": "🔻", "category": "structural",
        "description": "Many small → collect → scatter to many small again",
        "severity_default": "CRITICAL", "engine": "hybrid",
    },
    "WEEKEND_RUSH": {
        "name": "Weekend Rush", "icon": "📅", "category": "structural",
        "description": "Disproportionate volume on weekends vs weekdays",
        "severity_default": "MEDIUM", "engine": "sql",
    },
    "DORMANT_ACTIVATION": {
        "name": "Dormant Activation", "icon": "💤", "category": "structural",
        "description": "Zero-activity account suddenly active",
        "severity_default": "MEDIUM", "engine": "sql",
    },
    "CROSSBANK_HOP": {
        "name": "Cross-Bank Hop", "icon": "🏦", "category": "structural",
        "description": "Money traversing 4+ distinct banks before cash-out",
        "severity_default": "CRITICAL", "engine": "neo4j",
    },

    # ──── Scam Playbook Patterns (7) ─────────────────────────
    "INVESTMENT_SCAM": {
        "name": "Investment Scam", "icon": "🎯", "category": "scam_playbook",
        "description": "Escalating victim payments to same account over weeks",
        "severity_default": "CRITICAL", "engine": "sql",
    },
    "OTP_FRAUD": {
        "name": "OTP Fraud", "icon": "📱", "category": "scam_playbook",
        "description": "Small test transaction followed by full account drain",
        "severity_default": "CRITICAL", "engine": "sql",
    },
    "JOB_SCAM": {
        "name": "Job Scam", "icon": "💼", "category": "scam_playbook",
        "description": "Registration fee collection from many victims",
        "severity_default": "HIGH", "engine": "sql",
    },
    "ROMANCE_SCAM": {
        "name": "Romance Scam", "icon": "💕", "category": "scam_playbook",
        "description": "Irregular gifting timeline with increasing amounts",
        "severity_default": "HIGH", "engine": "sql",
    },
    "KYC_FRAUD": {
        "name": "KYC Fraud", "icon": "🪪", "category": "scam_playbook",
        "description": "Account details change followed by large transfer",
        "severity_default": "HIGH", "engine": "sql",
    },
    "CASHOUT_FINGERPRINT": {
        "name": "Cash-Out Fingerprint", "icon": "🏧", "category": "scam_playbook",
        "description": "ATM withdrawal pattern across multiple locations",
        "severity_default": "HIGH", "engine": "sql",
    },
    "MULTI_BANK_LAYERING": {
        "name": "Multi-Bank Layering", "icon": "🏦", "category": "scam_playbook",
        "description": "Money bouncing through 4+ different banks before cash-out",
        "severity_default": "CRITICAL", "engine": "neo4j",
    },
}


def get_all_pattern_types():
    """Return all pattern type definitions for the /types endpoint."""
    return [
        {
            "type_id": k,
            "name": v["name"],
            "icon": v["icon"],
            "description": v["description"],
            "severity_default": v["severity_default"],
            "engine": v["engine"],
            "category": v["category"],
        }
        for k, v in PATTERN_REGISTRY.items()
    ]

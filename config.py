"""
Shared configuration for keywords and risk scores.
Kept separate so both utils and pipeline can import them.
"""

DEFAULT_KEYWORDS = {
    "Data Collection": ["collect", "personal data", "information we collect", "analytic", "cookie"],
    "Data Sharing": ["share", "third party", "affiliate", "advertis", "partner"],
    "User Rights": ["access", "rectify", "delete", "opt-out", "withdraw consent"],
    "Restrictions": ["not permit", "prohibit", "you agree not to", "misuse", "reverse engineer"],
    "Termination": ["terminat", "suspend", "violation", "breach"],
    "Refunds & Billing": ["refund", "charge", "billing", "payment", "subscription"],
    "Dispute Resolution": ["arbitrat", "class action", "waive", "governing law", "venue"],
    "Liability & Warranty": ["warrant", "liab", "indemnify", "disclaim", "limit"],
}

RISK_SCORES = {
    # Using truncated keywords to catch variations
    "sell data": 5,
    "arbitrat": 3,      # Catches "arbitration"
    "class action": 3,
    "waive": 2,
    "indemnify": 3,
    "no refund": 3,
    "limit": 2,         # Catches "limitation"
    "share": 1,
    "high interest": 4,
    "penalty": 3,
}
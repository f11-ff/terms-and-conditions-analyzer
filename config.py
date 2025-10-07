"""
Shared configuration for keywords and risk scores.
Kept separate so both utils and pipeline can import them.
"""

DEFAULT_KEYWORDS = {
    "Data Collection": ["collect", "personal data", "information we collect", "analytics", "cookies"],
    "Data Sharing": ["share", "third party", "affiliate", "advertis", "partner"],
    "User Rights": ["access", "rectify", "delete", "opt-out", "withdraw consent"],
    "Restrictions": ["not permitted", "prohibited", "you agree not to", "misuse", "reverse engineer"],
    "Termination": ["terminate", "suspend", "violation", "breach"],
    "Refunds & Billing": ["refund", "charge", "billing", "payment", "subscription"],
    "Dispute Resolution": ["arbitration", "class action", "waive", "governing law", "venue"],
    "Liability & Warranty": ["warranty", "liability", "indemnify", "disclaim", "limitation"],
    # Banking-specific examples left out of default set (can be added)
}

RISK_SCORES = {
    "sell data": 5,
    "arbitration": 3,
    "class action": 3,
    "waive": 2,
    "indemnify": 3,
    "no refund": 3,
    "limitation": 2,
    "share": 1,
    "high interest": 4,
    "penalty": 3,
}

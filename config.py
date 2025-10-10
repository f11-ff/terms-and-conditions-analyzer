"""
Shared configuration for keywords and risk scores.
"""

DEFAULT_KEYWORDS = {
    "Data Collection": ["collect", "personal data", "information we collect", "analytic", "cookie"],
    "Data Sharing": ["share", "third party", "affiliate", "advertis", "partner"],
    "User Rights": ["access", "rectify", "delete", "opt-out", "withdraw consent"],
    "Restrictions": ["not permit", "prohibit", "you agree not to", "misuse", "reverse engineer"],
    "Termination": ["terminat", "suspend", "violation", "breach"],
    "Refunds & Billing": ["refund", "charge", "billing", "payment", "subscription", "auto-renewal", "hidden fee"],
    "Dispute Resolution": ["arbitrat", "class action", "waive", "governing law", "venue"],
    "Liability & Warranty": ["warrant", "liab", "indemnify", "disclaim", "limit"],
    "User Content Ownership": ["your content", "ownership", "grant license", "intellectual property", "upload"],
    "Third-party Integration": ["third-party", "integrate", "plugin", "external service"],
    "Security & Breach Responsibility": ["data breach", "unauthorized access", "security", "encrypt"],
}

RISK_SCORES = {
    "sell data": 5, "arbitrat": 3, "class action": 3, "waive": 2, "indemnify": 3,
    "no refund": 3, "limit": 2, "share": 1, "hidden fee": 3,
    "auto-renew": 3, "unauthorized access": 4, "data breach": 4,
    "monitor": 3, "suspend": 3,
}

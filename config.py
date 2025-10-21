"""
Shared configuration for keywords and risk scores.
Expanded with synonyms and common legal phrases for better detection.
"""

DEFAULT_KEYWORDS = {
    # --- Software ToS ---
    "Data Collection": ["collect", "personal data", "information we collect", "analytic", "cookie", "usage data", "telemetry"],
    "Data Sharing": ["share", "third party", "affiliate", "advertis", "partner", "disclose"],
    "User Rights": ["access", "rectify", "delete", "opt-out", "withdraw consent", "your rights", "data portability"],
    "Restrictions": ["not permit", "prohibit", "you agree not to", "misuse", "reverse engineer", "unauthorized use"],
    "Termination": ["terminat", "suspend", "cancel", "close account", "end this agreement", "violation", "breach"],
    "Refunds & Billing": ["refund", "charge", "billing", "payment", "subscription", "auto-renewal", "hidden fee", "no refunds"],
    "Dispute Resolution": ["arbitrat", "class action", "waive", "governing law", "venue", "dispute"],
    "Liability & Warranty": ["warrant", "liab", "indemnify", "disclaim", "as is", "no warranty", "limit our liability"],
    "User Content Ownership": ["your content", "ownership", "you grant", "license", "intellectual property", "upload"],
    "Third-party Integration": ["third-party", "integrate", "plugin", "external service"],
    "Security & Breach Responsibility": ["data breach", "unauthorized access", "security", "encrypt"],
    
    # --- Rental / Lease Agreement ---
    "Lease Terms & Duration": ["lease term", "duration", "month-to-month", "fixed-term", "renewal", "notice to vacate"],
    "Financials (Rent, Fees, Deposit)": ["rent", "due on", "late fee", "security deposit", "pet deposit", "non-refundable", "additional charges"],
    "Responsibilities & Rules": ["maintenance", "repairs", "utilities", "tenant responsible", "landlord responsible", "sublet", "subleasing", "pets", "alterations"],
    "Lease Termination": ["early termination", "break lease", "notice period", "eviction", "abandonment"],

    # --- Insurance Policy ---
    "Coverage & Limits": ["coverage", "covered loss", "limit of liability", "personal property", "dwelling", "policy limit"],
    "Exclusions (What's Not Covered)": ["exclusion", "not cover", "wear and tear", "pre-existing condition", "act of god", "we do not cover"],
    "Premiums & Payments": ["premium", "deductible", "due date", "cancellation for non-payment", "grace period"],
    "Claims & Procedures": ["claim", "proof of loss", "notice", "deadline", "adjuster", "filing a claim"],

    # --- Loan Agreement ---
    "Loan Terms (Principal, Interest)": ["principal amount", "interest rate", "apr", "annual percentage rate", "variable rate", "fixed rate"],
    "Repayment Schedule": ["repayment", "monthly payment", "term of loan", "maturity date", "amortization", "installments"],
    "Fees & Penalties": ["late payment", "prepayment penalty", "origination fee", "closing cost", "additional fees"],
    "Collateral & Default": ["collateral", "security", "default", "acceleration", "lien", "repossession", "failure to pay"],
}

RISK_SCORES = {
    # --- General High-Risk ---
    "sell data": 5, "arbitrat": 3, "class action": 3, "waive": 2, "indemnify": 3,
    "unauthorized access": 4, "data breach": 4, "monitor": 3, "suspend": 3,
    
    # --- Financial High-Risk ---
    "no refund": 3, "hidden fee": 3, "auto-renew": 3, "late fee": 3,
    "prepayment penalty": 4, "variable rate": 3, "acceleration": 5, "default": 4,
    
    # --- Rights & Liability High-Risk ---
    "limit our liability": 3, "share": 1, "non-refundable": 4, "pre-existing condition": 4, "exclusion": 3,
    "repossession": 5, "as is": 3, "no warranty": 4,
}


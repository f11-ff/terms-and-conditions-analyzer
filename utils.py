"""
Utility helper functions for text processing and risk tagging.
"""
import re
from typing import List, Tuple, Dict, Any
from config import DEFAULT_KEYWORDS, RISK_SCORES

def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    if not text: return ""
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def sentences(text: str) -> List[str]:
    """Split text into sentences."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def tag_sentence(sentence: str, keywords: Dict[str, List[str]] = None) -> Dict[str, List[str]]:
    """✅ Tags a sentence and returns the specific keywords that were matched for each category."""
    if keywords is None: keywords = DEFAULT_KEYWORDS
    s_lower = sentence.lower()
    hits = {}
    for cat, kws in keywords.items():
        matched_kws = [kw for kw in kws if kw.lower() in s_lower]
        if matched_kws:
            hits[cat] = matched_kws
    return hits

def risk_for_sentence(sentence: str) -> Tuple[int, List[str]]:
    """Compute risk score and high-risk triggers (for scoring only)."""
    s_lower = sentence.lower()
    score = 0
    risk_triggers = []
    for kw, pts in RISK_SCORES.items():
        if kw in s_lower:
            score += pts
            risk_triggers.append(kw)
    return score, risk_triggers

def band(score: int) -> str:
    """Convert numerical score to risk band."""
    if score >= 6: return "High"
    if score >= 3: return "Medium"
    return "Low"

def provenance_dict(snippet: str, location: str) -> Dict[str, str]:
    """Generate provenance info for each clause."""
    return {"snippet": snippet, "location": location}
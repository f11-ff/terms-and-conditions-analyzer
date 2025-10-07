# utils.py
"""
Utility helper functions for text processing and risk tagging.
All low-level helpers live here to avoid duplication.
"""

import re
from typing import List, Tuple, Dict, Any
from dataclasses import asdict

from config import DEFAULT_KEYWORDS, RISK_SCORES


def sentences(text: str) -> List[str]:
    """
    Split text into sentences (lightweight splitter).
    Returns list of non-empty sentences.
    """
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def tag_sentence(sentence: str, keywords: Dict[str, List[str]] = None) -> List[str]:
    """
    Return list of categories whose keywords match the sentence.
    Case-insensitive substring match.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
    s = sentence.lower()
    hits = []
    for cat, kws in keywords.items():
        for kw in kws:
            if kw.lower() in s:
                hits.append(cat)
                break
    return hits


def risk_for_sentence(sentence: str) -> Tuple[int, List[str]]:
    """
    Compute a numeric risk score and list of triggers for a sentence using RISK_SCORES.
    Returns (score, triggers).
    """
    s = sentence.lower()
    score = 0
    triggers = []
    for kw, pts in RISK_SCORES.items():
        if kw in s:
            score += pts
            triggers.append(kw)
    return score, triggers


def band(score: int) -> str:
    """
    Convert numeric score to band label: High / Medium / Low.
    """
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def provenance_dict(snippet: str, location: str) -> Dict[str, str]:
    """Return a provenance dictionary for a snippet location pair."""
    return {"snippet": snippet, "location": location}


def bullets_to_dicts(bullets: List[Any]) -> List[Dict[str, Any]]:
    """
    Convert list of dataclass-like objects to list of dicts. Useful if you ever use dataclasses.
    Currently retains passed dicts as-is.
    """
    out = []
    for b in bullets:
        try:
            out.append(asdict(b))
        except Exception:
            # already a dict
            out.append(b)
    return out

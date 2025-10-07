"""
Main document processing pipeline.
Uses utils and config. Returns normalized dictionary:
{
  "ai_summary": str,
  "categories": [ {"category": str, "bullets": [ { "text", "risk", "rationale", "provenance" }, ... ] }, ... ],
  "raw_text": str
}
"""

from transformers import pipeline
from typing import Dict, Any, List
from utils import sentences, tag_sentence, risk_for_sentence, band, provenance_dict
from config import DEFAULT_KEYWORDS

# -------------------------
# 🔹 Summarizer setup
# -------------------------
# Load HuggingFace summarization model once
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize_text(text: str, max_len=60) -> str:
    """
    Run summarization on a short text using a lightweight model.
    """
    text = text.strip()
    if not text:
        return ""
    try:
        res = summarizer(text[:2000], max_length=max_len, min_length=20, do_sample=False)
        return res[0]["summary_text"].strip()
    except Exception:
        # Fallback: show truncated text if summarizer fails
        return text[:150] + "..."

# -------------------------
# 🔹 Main pipeline
# -------------------------
def process_document(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the provided text and return a structured summary dictionary.
    """
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    categories = config.get("categories", [])
    max_bullets = int(config.get("max_bullets_per_category", 6))

    sents = sentences(text)
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}

    # Sentence-level tagging
    for idx, s in enumerate(sents, start=1):
        cats = tag_sentence(s, keywords)
        if not cats:
            continue
        score, triggers = risk_for_sentence(s)
        band_label = band(score)

        # Try to preserve any [Page X, Line Y] tag if present
        if s.startswith("[Page"):
            location = s.split("]")[0].strip("[")  # e.g. "Page 2, Line 15"
        else:
            location = f"line {idx}"

        for cat in cats:
            if cat not in per_cat:
                continue
            per_cat[cat].append({
                "text": s,
                "risk": band_label,
                "rationale": triggers,
                "provenance": provenance_dict("", location),
                "score": score
            })

    # Category summarization
    categories_out: List[Dict[str, Any]] = []
    for cat in categories:
        items = sorted(per_cat.get(cat, []), key=lambda x: (-x["score"], x["text"]))
        seen_texts = set()
        bullets = []
        for item in items:
            if item["text"] in seen_texts:
                continue
            seen_texts.add(item["text"])

            # 🔹 Summarize each bullet instead of showing full sentence
            short_summary = summarize_text(item["text"], max_len=50)

            bullets.append({
                "text": short_summary,
                "risk": item["risk"],
                "rationale": item["rationale"],
                "provenance": item["provenance"],
            })
            if len(bullets) >= max_bullets:
                break

        categories_out.append({"category": cat, "bullets": bullets})

    # 🔹 Global concise summary (2–4 lines)
    # Join top sentences or summaries from categories and re-summarize
    all_text_for_global = " ".join(
        [b["text"] for c in categories_out for b in c["bullets"][:2]]
    )
    ai_summary = summarize_text(all_text_for_global, max_len=80)

    return {
        "ai_summary": ai_summary,
        "categories": categories_out,
        "raw_text": text
    }

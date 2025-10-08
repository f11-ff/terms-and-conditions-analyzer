"""
Main document processing pipeline.
Uses utils and config. Returns normalized dictionary:
{
  "ai_summary": str,
  "categories": [ {"category": str, "category_summary": str, "bullets": [ { "text", "risk", "rationale", "provenance" }, ... ] }, ... ],
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
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize_text(text: str, max_len=80, min_len=20) -> str:
    """Run summarization on text using a lightweight model."""
    text = text.strip()
    if len(text) < 40: # Don't summarize very short text
        return text
    try:
        # Limit input length to avoid overwhelming the model
        res = summarizer(text[:2048], max_length=max_len, min_length=min_len, do_sample=False)
        return res[0]["summary_text"].strip()
    except Exception:
        return text[:250] + "..." # Fallback

# -------------------------
# 🔹 Main pipeline (Optimized)
# -------------------------
def process_document(text: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Process the provided text and return a structured summary dictionary."""
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    categories = config.get("categories", [])
    max_bullets = int(config.get("max_bullets_per_category", 5))

    sents = sentences(text)
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}

    # Sentence-level tagging
    for idx, s in enumerate(sents, start=1):
        cats = tag_sentence(s, keywords)
        if not cats:
            continue
        score, triggers = risk_for_sentence(s)
        band_label = band(score)

        if s.startswith("[Page"):
            location = s.split("]")[0].strip("[")
        else:
            location = f"line {idx}"
        
        # Remove the location tag for cleaner processing
        clean_sentence = s.split("]", 1)[-1].strip()

        for cat in cats:
            if cat in per_cat:
                per_cat[cat].append({
                    "text": clean_sentence,
                    "risk": band_label,
                    "rationale": triggers,
                    "provenance": provenance_dict(s, location),
                    "score": score
                })

    # Category-level summarization (Optimized to reduce AI calls)
    categories_out: List[Dict[str, Any]] = []
    all_top_clauses_text = []

    for cat in categories:
        # Sort clauses by risk score to find the most important ones
        items = sorted(per_cat.get(cat, []), key=lambda x: -x["score"])
        
        # Get unique top clauses to summarize
        seen_texts = set()
        top_clauses = []
        for item in items:
            if item["text"] not in seen_texts:
                top_clauses.append(item)
                seen_texts.add(item["text"])
            if len(top_clauses) >= max_bullets:
                break
        
        category_summary = ""
        if top_clauses:
            # Join the text of the most important clauses for a single summary call
            text_for_summary = " ".join([c["text"] for c in top_clauses])
            category_summary = summarize_text(text_for_summary, max_len=60, min_len=15)
            all_top_clauses_text.append(text_for_summary)

        categories_out.append({
            "category": cat,
            "category_summary": category_summary,
            "bullets": top_clauses  # Bullets are now the full, original clauses
        })

    # Global concise summary (2–4 lines) based on all top clauses
    global_summary_text = " ".join(all_top_clauses_text)
    ai_summary = summarize_text(global_summary_text, max_len=100, min_len=30)

    return {
        "ai_summary": ai_summary,
        "categories": categories_out,
        "raw_text": text
    }
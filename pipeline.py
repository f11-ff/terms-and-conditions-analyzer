"""
Main document processing pipeline (v0.5).
Calculates category-level risk and deterministically sets clause counts.
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
    if len(text) < 40:
        return text
    try:
        res = summarizer(text[:2048], max_length=max_len, min_length=min_len, do_sample=False)
        return res[0]["summary_text"].strip()
    except Exception:
        return text[:250] + "..."

# -------------------------
# 🔹 Main pipeline (Optimized)
# -------------------------
def process_document(text_pages: Dict[int, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Process text (split by page) and return a structured summary."""
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    categories = config.get("categories", [])
    
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}
    raw_text_full = ""

    # Sentence-level tagging, now aware of page numbers
    for page_num, page_text in text_pages.items():
        raw_text_full += f"\n--- Page {page_num} ---\n{page_text}"
        sents = sentences(page_text)
        for s in sents:
            cats = tag_sentence(s, keywords)
            if not cats:
                continue
            
            score, triggers = risk_for_sentence(s)
            band_label = band(score)
            location = f"Page {page_num}"

            for cat in cats:
                if cat in per_cat:
                    per_cat[cat].append({
                        "text": s,
                        "risk": band_label,
                        "rationale": triggers,
                        "provenance": provenance_dict(s, location),
                        "score": score
                    })

    # Category-level summarization and risk calculation
    categories_out: List[Dict[str, Any]] = []
    all_top_clauses_text = []

    for cat in categories:
        items = sorted(per_cat.get(cat, []), key=lambda x: -x["score"])
        
        # ✅ Deterministically set max clauses based on findings
        # Show more clauses for categories with more findings, up to a max of 7
        max_bullets = min(7, 2 + len(items) // 4)

        seen_texts = set()
        top_clauses = []
        for item in items:
            if item["text"] not in seen_texts:
                top_clauses.append(item)
                seen_texts.add(item["text"])
            if len(top_clauses) >= max_bullets:
                break
        
        category_summary = ""
        category_risk = "Low" # Default risk
        if top_clauses:
            text_for_summary = " ".join([c["text"] for c in top_clauses])
            category_summary = summarize_text(text_for_summary, max_len=60, min_len=15)
            all_top_clauses_text.append(text_for_summary)

            # ✅ Calculate overall category risk (highest risk of its clauses)
            scores = {"High": 3, "Medium": 2, "Low": 1}
            top_risk_in_cat = max([c["risk"] for c in top_clauses], key=lambda r: scores[r])
            category_risk = top_risk_in_cat

        categories_out.append({
            "category": cat,
            "category_summary": category_summary,
            "category_risk": category_risk,
            "bullets": top_clauses
        })

    global_summary_text = " ".join(all_top_clauses_text)
    ai_summary = summarize_text(global_summary_text, max_len=100, min_len=30)

    return {
        "ai_summary": ai_summary,
        "categories": categories_out,
        "raw_text": raw_text_full.strip()
    }
"""
Main document processing pipeline (v1.2 – Improved Prompts).
- Uses a distinct, high-level prompt for the overall summary to avoid repetition.
"""
from transformers import pipeline
from typing import Dict, Any, List
from utils import sentences, tag_sentence, risk_for_sentence, band, provenance_dict, clean_text
from config import DEFAULT_KEYWORDS

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text_for_risk(category: str, text: str) -> str:
    """Summarize a category section focusing on user risk."""
    text = text.strip()
    if len(text) < 50: return f"This section on {category.lower()} may contain important clauses."
    prompt = (f"Summarize how the following clauses about {category} could impact user rights, privacy, or finances:\n\n{text[:3000]}")
    try:
        res = summarizer(prompt, max_length=120, min_length=30, do_sample=False)
        return res[0]["summary_text"].strip()
    except Exception: return f"Summary not available for {category.lower()}."

def create_global_summary(text: str) -> str:
    """✅ Uses a new, more sophisticated prompt for a high-level summary."""
    text = text.strip()
    if len(text) < 50: return "The document contains several clauses of interest across different categories."
    prompt = (
        "Create a high-level, executive summary of the most important takeaways from this document. "
        "Focus on the key permissions the user is granting and the most significant rights they have. "
        f"Do not simply repeat the introductory sentences.\n\nText:\n{text[:3000]}"
    )
    try:
        res = summarizer(prompt, max_length=150, min_length=40, do_sample=False)
        return res[0]["summary_text"].strip()
    except Exception: return "Could not generate an overall summary."

def process_document(text_pages: Dict[int, str], config: Dict[str, Any]) -> Dict[str, Any]:
    # (The first part of this function is unchanged)
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    categories = list(keywords.keys())
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}
    full_cleaned_text = ""

    for page_num, page_text in text_pages.items():
        cleaned_page_text = clean_text(page_text or "")
        full_cleaned_text += f"\n--- Page {page_num} ---\n{cleaned_page_text}"
        sents = sentences(cleaned_page_text)
        for s in sents:
            matched_cats = tag_sentence(s, keywords)
            if not matched_cats: continue
            score, _ = risk_for_sentence(s)
            for cat, triggers in matched_cats.items():
                per_cat[cat].append({
                    "text": s, "risk": band(score), "rationale": triggers,
                    "provenance": provenance_dict(s, f"Page {page_num}"), "score": score
                })

    categories_out: List[Dict[str, Any]] = []
    all_top_clauses = []
    for cat in categories:
        items = sorted(per_cat.get(cat, []), key=lambda x: -x["score"])
        if not items: continue
        unique_clauses = list({item['text']: item for item in items}.values())
        top_clauses = unique_clauses[:min(7, len(unique_clauses))]
        text_for_summary = " ".join([c["text"] for c in top_clauses])
        category_summary = summarize_text_for_risk(cat, text_for_summary)
        all_top_clauses.extend(top_clauses)
        if top_clauses:
            category_risk = max([c["risk"] for c in top_clauses], key=lambda r: {"High":3,"Medium":2,"Low":1}[r])
            categories_out.append({
                "category": cat, "category_summary": category_summary,
                "category_risk": category_risk, "bullets": top_clauses
            })

    # ✅ Call the new global summary function with its unique prompt
    unique_all_top = list({item['text']: item for item in all_top_clauses}.values())
    ai_summary = create_global_summary(" ".join([c['text'] for c in unique_all_top]))

    return {
        "ai_summary": ai_summary,
        "categories": categories_out,
        "raw_text": full_cleaned_text.strip()
    }
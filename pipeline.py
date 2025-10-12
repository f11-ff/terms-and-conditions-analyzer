# pipeline.py

"""
Main document processing pipeline (v1.7 – Robust Summaries).
- Added safety checks to summarization functions to prevent crashes on empty results.
- Retains all previous features like risk profiling and custom configs.
"""
from transformers import pipeline
from typing import Dict, Any, List
from utils import sentences, tag_sentence, risk_for_sentence, band, provenance_dict, clean_text

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def _safe_summarize(prompt: str, max_len: int, min_len: int) -> str:
    """A robust, internal summarization function with error handling."""
    try:
        res = summarizer(prompt, max_length=max_len, min_length=min_len, do_sample=False)
        # Safety Check: Ensure the result is not empty and has the expected key
        summary = res[0].get("summary_text") if res and isinstance(res, list) and res[0] else None
        return summary.strip() if summary else "AI summary could not be generated for this section."
    except Exception:
        return "An error occurred during AI summarization."

def summarize_text_for_risk(category: str, text: str) -> str:
    """Summarize a category section focusing on user risk."""
    text = text.strip()
    if len(text) < 50:
        return f"This section on {category.lower()} may contain important clauses but is too short to summarize."
    prompt = (f"Summarize how the following clauses about {category} could impact user rights, privacy, or finances:\n\n{text[:3000]}")
    return _safe_summarize(prompt, 120, 30)

def create_global_summary(text: str) -> str:
    """Uses a more sophisticated prompt for a high-level summary."""
    text = text.strip()
    if len(text) < 50:
        return "The document contains several clauses of interest but is too short for a global summary."
    prompt = (
        "Create a high-level, executive summary of the most important takeaways from this document. "
        "Focus on the key permissions the user is granting and the most significant rights they have. "
        f"Do not simply repeat the introductory sentences.\n\nText:\n{text[:3000]}"
    )
    return _safe_summarize(prompt, 150, 40)

def process_document(text_pages: Dict[int, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Main document analysis pipeline."""
    keywords = config.get("keywords", {})
    categories = config.get("categories", [])
    risk_scores = config.get("risk_scores", {})
    
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}
    full_cleaned_text = ""

    for page_num, page_text in text_pages.items():
        cleaned_page_text = clean_text(page_text or "")
        full_cleaned_text += f"\n--- Page {page_num} ---\n{cleaned_page_text}"
        sents = sentences(cleaned_page_text)
        for s in sents:
            matched_cats = tag_sentence(s, keywords)
            if not matched_cats: continue
            score, _ = risk_for_sentence(s, risk_scores)
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

    unique_all_top = list({item['text']: item for item in all_top_clauses}.values())
    ai_summary = create_global_summary(" ".join([c['text'] for c in unique_all_top]))
    
    total_clauses = len(unique_all_top)
    weighted_score = 0
    if total_clauses > 0:
        for clause in unique_all_top:
            if clause["risk"] == "High": weighted_score += 3
            elif clause["risk"] == "Medium": weighted_score += 2
            else: weighted_score += 1
        max_possible_score = total_clauses * 3
        overall_risk_score = (weighted_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    else:
        overall_risk_score = 0

    return {
        "ai_summary": ai_summary,
        "categories": categories_out,
        "raw_text": full_cleaned_text.strip(),
        "overall_risk_score": overall_risk_score
    }

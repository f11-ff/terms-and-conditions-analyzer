"""
Main document processing pipeline (v1.1 – Final).
- Uses improved trigger logic from utils.
- Ensures every clause has a clear rationale.
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

def process_document(text_pages: Dict[int, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Main document analysis pipeline."""
    keywords = config.get("keywords", DEFAULT_KEYWORDS)
    categories = list(keywords.keys())
    per_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in categories}
    full_cleaned_text = ""

    for page_num, page_text in text_pages.items():
        cleaned_page_text = clean_text(page_text or "")
        full_cleaned_text += f"\n--- Page {page_num} ---\n{cleaned_page_text}"
        sents = sentences(cleaned_page_text)

        for s in sents:
            # ✅ Get the dictionary of matched categories and their specific trigger keywords
            matched_cats = tag_sentence(s, keywords)
            if not matched_cats: continue
            
            score, _ = risk_for_sentence(s) # Score is still calculated from high-risk words
            
            for cat, triggers in matched_cats.items():
                per_cat[cat].append({
                    "text": s,
                    "risk": band(score),
                    "rationale": triggers, # ✅ The rationale is now the keyword that categorized the clause
                    "provenance": provenance_dict(s, f"Page {page_num}"),
                    "score": score
                })

    categories_out: List[Dict[str, Any]] = []
    all_top_clauses = []
    for cat in categories:
        items = sorted(per_cat.get(cat, []), key=lambda x: -x["score"])
        if not items: continue

        # De-duplicate clauses to avoid repetition
        unique_clauses = list({item['text']: item for item in items}.values())
        top_clauses = unique_clauses[:min(7, len(unique_clauses))]
        
        text_for_summary = " ".join([c["text"] for c in top_clauses])
        category_summary = summarize_text_for_risk(cat, text_for_summary)
        all_top_clauses.extend(top_clauses)
        
        if top_clauses:
            category_risk = max([c["risk"] for c in top_clauses], key=lambda r: {"High":3,"Medium":2,"Low":1}[r])
            categories_out.append({
                "category": cat,
                "category_summary": category_summary,
                "category_risk": category_risk,
                "bullets": top_clauses
            })

    unique_all_top = list({item['text']: item for item in all_top_clauses}.values())
    ai_summary = summarize_text_for_risk("the overall document", " ".join([c['text'] for c in unique_all_top]))

    return {
        "ai_summary": ai_summary,
        "categories": categories_out,
        "raw_text": full_cleaned_text.strip()
    }
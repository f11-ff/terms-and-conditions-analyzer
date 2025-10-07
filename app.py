"""
Streamlit frontend for Terms & Conditions Analyzer (v0.3 beta).
Uses pipeline.process_document and utils for text processing.
"""

import io
import json
import re
import sqlite3
from typing import Dict, Any, Optional

import streamlit as st

# Optional PDF
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

# Optional OCR
try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None

from pipeline import process_document
from config import DEFAULT_KEYWORDS

# -------------------------
# App version
# -------------------------
APP_VERSION = "v0.3 beta"

# -------------------------
# Category sets
# -------------------------
CATEGORY_SETS = {
    "Software ToS": [
        "Data Collection", "Data Sharing", "User Rights", "Restrictions",
        "Termination", "Refunds & Billing", "Dispute Resolution", "Liability & Warranty"
    ]
}

# -------------------------
# Utility functions for app
# -------------------------
def _extract_text_from_pdf(file: bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # Tag each line with its page for provenance
        lines = [f"[Page {i}, Line {ln+1}] {line}" for ln, line in enumerate(text.splitlines()) if line.strip()]
        pages.append("\n".join(lines))
    return "\n".join(pages)


def _simple_sentences(text: str):
    """Local lightweight sentence splitter used for search & highlight."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


# -------------------------
# SQLite persistence
# -------------------------
def init_db():
    conn = sqlite3.connect("analyses.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY,
                  doc_type TEXT,
                  raw_text TEXT,
                  summary_json TEXT)""")
    conn.commit()
    return conn


def save_analysis(doc_type, raw_text, summary):
    conn = init_db()
    conn.execute("INSERT INTO documents (doc_type, raw_text, summary_json) VALUES (?, ?, ?)",
                 (doc_type, raw_text, json.dumps(summary)))
    conn.commit()


def load_past_analyses():
    conn = init_db()
    return conn.execute("SELECT id, doc_type FROM documents ORDER BY id DESC").fetchall()


def load_analysis_by_id(doc_id: int):
    conn = init_db()
    row = conn.execute("SELECT summary_json FROM documents WHERE id=?", (doc_id,)).fetchone()
    return json.loads(row[0]) if row else None


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Terms Analyzer", page_icon="⚖️", layout="wide")
st.title("⚖️ Terms & Conditions Analyzer")

# Sidebar (version + settings)
with st.sidebar:
    st.header("Settings")
    st.markdown(f"**Version:** {APP_VERSION}")
    selected_set = st.selectbox("Document Type", list(CATEGORY_SETS.keys()))
    max_bullets = st.slider("Max bullets per category", 3, 10, 6)
    st.write("")  # spacer
    st.subheader("Past Analyses")
    past = load_past_analyses()
    if past:
        for doc_id, doc_type in past:
            if st.button(f"Load {doc_type} #{doc_id}"):
                st.session_state["result"] = load_analysis_by_id(doc_id)

# Inputs
st.header("📥 Input Document")
col1, col2 = st.columns(2)

with col1:
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
with col2:
    pasted = st.text_area("Or paste text", height=300, placeholder="Paste terms or agreement text here…")

run_btn = st.button("▶ Run Analyzer")

# Decide input source (prefer uploaded file over pasted text)
text = ""
if uploaded_pdf:
    text = _extract_text_from_pdf(uploaded_pdf.getvalue())
elif pasted and pasted.strip():
    text = pasted.strip()

# Run pipeline
if run_btn:
    if not text:
        st.warning("Please upload a PDF, or paste text.")
    else:
        with st.spinner("Processing document…"):
            config = {
                "categories": CATEGORY_SETS[selected_set],
                "keywords": DEFAULT_KEYWORDS,
                "max_bullets_per_category": max_bullets
            }
            try:
                data = process_document(text, config)
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                data = None
        if data:
            # normalized dict guaranteed by pipeline
            st.session_state["result"] = data
            save_analysis(selected_set, text, data)

# Results
result: Optional[Dict[str, Any]] = st.session_state.get("result")
if result:
    tabs = st.tabs(["Summary", "Clauses/Search", "JSON", "Export"])

    with tabs[0]:
        st.subheader("AI Summary")
        ai_summary = result.get("ai_summary", "")
        if ai_summary:
            st.success(ai_summary)
        else:
            st.info("No AI summary available for this document.")

        st.subheader("Key Terms & Risks")
        for category_summary in result.get("categories", []):
            if not category_summary.get("bullets"):
                continue
            with st.expander(f"**{category_summary.get('category','Unnamed')}**"):
                for bullet in category_summary.get("bullets", []):
                    risk_color = "red" if bullet.get('risk') == "High" else "orange" if bullet.get('risk') == "Medium" else "green"
                    st.markdown(
                        f"- <span style='color:{risk_color}; font-weight:bold;'>{bullet.get('risk')} Risk:</span> {bullet.get('text')}",
                        unsafe_allow_html=True
                    )

                    # ✅ Updated Details section (shows only location, not the entire dict)
                    with st.expander("Details"):
                        prov = bullet.get("provenance", {})
                        if isinstance(prov, list):
                            prov = prov[0] if prov else {}
                        loc = prov.get("location", "Unknown")
                        st.write(f"📍 **Location:** {loc}")

    with tabs[1]:
        st.subheader("Search & Highlight Clauses")
        search_query = st.text_input("Enter a keyword to find relevant clauses")
        if search_query:
            sentences = _simple_sentences(result.get("raw_text", ""))
            matches = [s for s in sentences if search_query.lower() in s.lower()]
            st.markdown(f"**Found {len(matches)} matches.**")
            for s in matches:
                st.info(s)

    with tabs[2]:
        st.subheader("Raw JSON Output")
        st.json(result)

    with tabs[3]:
        st.subheader("Export")
        st.download_button(
            "Download Analysis as JSON",
            data=json.dumps(result, indent=4),
            file_name="analysis.json",
            mime="application/json"
        )
else:
    st.info("Upload a PDF, or paste text, then click **Run Analyzer**.")

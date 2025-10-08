"""
Streamlit frontend for Terms & Conditions Analyzer (v0.4 optimized).
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

from pipeline import process_document
from config import DEFAULT_KEYWORDS

# -------------------------
# App version
# -------------------------
APP_VERSION = "v0.4 optimized"

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
    if not PyPDF2:
        st.error("PyPDF2 is not installed. Please install it to read PDFs.")
        return ""
    reader = PyPDF2.PdfReader(io.BytesIO(file))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        lines = [f"[Page {i}] {line}" for line in text.splitlines() if line.strip()]
        pages.append("\n".join(lines))
    return "\n".join(pages)


def _simple_sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


# -------------------------
# SQLite persistence
# -------------------------
def init_db():
    conn = sqlite3.connect("analyses.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY, doc_type TEXT, raw_text TEXT, summary_json TEXT)""")
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

with st.sidebar:
    st.header("Settings")
    st.markdown(f"**Version:** {APP_VERSION}")
    selected_set = st.selectbox("Document Type", list(CATEGORY_SETS.keys()))
    max_bullets = st.slider("Max clauses per category", 2, 8, 4)
    st.write("")
    st.subheader("Past Analyses")
    past = load_past_analyses()
    if past:
        for doc_id, doc_type in past:
            if st.button(f"Load {doc_type} #{doc_id}"):
                st.session_state["result"] = load_analysis_by_id(doc_id)

st.header("📥 Input Document")
pasted = st.text_area("Paste text here", height=250, placeholder="Paste terms or agreement text here…")
uploaded_pdf = st.file_uploader("Or upload PDF", type=["pdf"])

run_btn = st.button("▶ Run Analyzer")

text = ""
if uploaded_pdf:
    text = _extract_text_from_pdf(uploaded_pdf.getvalue())
elif pasted and pasted.strip():
    text = pasted.strip()

if run_btn:
    if not text:
        st.warning("Please upload a PDF or paste some text.")
    else:
        with st.spinner("Processing document… This may take a moment."):
            config = {
                "categories": CATEGORY_SETS[selected_set],
                "keywords": DEFAULT_KEYWORDS,
                "max_bullets_per_category": max_bullets
            }
            try:
                data = process_document(text, config)
                st.session_state["result"] = data
                save_analysis(selected_set, text, data)
            except Exception as e:
                st.error(f"An error occurred in the pipeline: {e}")

result: Optional[Dict[str, Any]] = st.session_state.get("result")
if result:
    tabs = st.tabs(["Summary", "Clauses/Search", "JSON Output"])

    with tabs[0]:
        st.subheader("Overall AI Summary")
        st.info(result.get("ai_summary", "No overall summary could be generated."))

        st.subheader("Key Clauses by Category")
        for category_summary in result.get("categories", []):
            cat_name = category_summary.get('category', 'Unnamed')
            with st.expander(f"**{cat_name}**"):
                st.success(f"**Category Summary:** {category_summary.get('category_summary', 'N/A')}")
                
                # Display the full original clauses as bullets
                for bullet in category_summary.get("bullets", []):
                    risk_color = "red" if bullet.get('risk') == "High" else "orange" if bullet.get('risk') == "Medium" else "green"
                    st.markdown(
                        f"<p style='color:{risk_color}; margin-bottom: 2px;'><b>{bullet.get('risk')} Risk Clause:</b></p>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"> {bullet.get('text')}")

                    # Enhanced details section
                    with st.expander("Details"):
                        prov = bullet.get("provenance", {})
                        rationale = bullet.get("rationale", [])
                        st.write(f"📍 **Location:** {prov.get('location', 'Unknown')}")
                        st.write(f"🤔 **Risk Rationale:** Triggered by keyword(s) - `{', '.join(rationale)}`")

    with tabs[1]:
        st.subheader("Search & Highlight Clauses")
        search_query = st.text_input("Enter keyword to find relevant clauses")
        if search_query:
            sentences = _simple_sentences(result.get("raw_text", ""))
            matches = [s for s in sentences if search_query.lower() in s.lower()]
            st.markdown(f"**Found {len(matches)} matches.**")
            for s in matches:
                st.info(s)

    with tabs[2]:
        st.subheader("Raw JSON Output")
        st.json(result)

else:
    st.info("Paste text or upload a document, then click **Run Analyzer**.")
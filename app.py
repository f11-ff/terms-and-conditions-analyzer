"""
Streamlit frontend for Terms & Conditions Analyzer (v0.5 UI Refresh).
"""

import io
import json
import re
import sqlite3
from typing import Dict, Any, Optional

import streamlit as st

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

from pipeline import process_document
from config import DEFAULT_KEYWORDS

# App version
APP_VERSION = "v0.5 UI Refresh"

CATEGORY_SETS = {
    "Software ToS": [
        "Data Collection", "Data Sharing", "User Rights", "Restrictions",
        "Termination", "Refunds & Billing", "Dispute Resolution", "Liability & Warranty"
    ]
}

# -------------------------
# Utility Functions
# -------------------------
def _extract_text_from_pdf(file_bytes: bytes) -> Dict[int, str]:
    """Extracts text from a PDF, returning a dictionary of page_num: text."""
    if not PyPDF2:
        st.error("PyPDF2 is not installed. PDF processing is disabled.")
        return {}
    pages = {}
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text and text.strip():
            pages[i] = text
    return pages

def _format_analysis_for_export(result: Dict[str, Any]) -> str:
    """Formats the analysis into a clean text/markdown string."""
    lines = [f"# Analysis Summary\n"]
    lines.append(f"## Overall AI Summary\n{result.get('ai_summary', 'N/A')}\n")
    lines.append("## Key Clauses by Category\n")
    
    for cat in result.get("categories", []):
        lines.append(f"### {cat.get('category')} (Risk: {cat.get('category_risk')})")
        lines.append(f"**Summary:** {cat.get('category_summary', 'N/A')}\n")
        for bullet in cat.get('bullets', []):
            lines.append(f"- **({bullet.get('risk')} Risk):** {bullet.get('text')}")
            lines.append(f"  - *Location:* {bullet['provenance'].get('location', 'Unknown')}")
            lines.append(f"  - *Triggers:* {', '.join(bullet.get('rationale', []))}\n")
    return "\n".join(lines)

# (Database functions like init_db, save_analysis, etc. remain unchanged)
def init_db():
    conn = sqlite3.connect("analyses.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY, doc_type TEXT, summary_json TEXT)""")
    conn.commit()
    return conn

def save_analysis(doc_type, summary):
    conn = init_db()
    conn.execute("INSERT INTO documents (doc_type, summary_json) VALUES (?, ?)",
                 (doc_type, json.dumps(summary)))
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
    st.write("---")
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

text_pages = {}
if uploaded_pdf:
    text_pages = _extract_text_from_pdf(uploaded_pdf.getvalue())
elif pasted and pasted.strip():
    text_pages = {1: pasted.strip()} # Treat pasted text as a single page

if run_btn:
    if not text_pages:
        st.warning("Please upload a PDF or paste some text.")
    else:
        with st.spinner("Processing document… This may take a moment."):
            config = {"categories": CATEGORY_SETS[selected_set], "keywords": DEFAULT_KEYWORDS}
            try:
                data = process_document(text_pages, config)
                st.session_state["result"] = data
                save_analysis(selected_set, data)
            except Exception as e:
                st.error(f"An error occurred in the pipeline: {e}")

result: Optional[Dict[str, Any]] = st.session_state.get("result")
if result:
    tabs = st.tabs(["📊 Summary", "📄 Clauses/Search", "📥 Export"])

    with tabs[0]:
        st.subheader("Overall AI Summary")
        st.info(result.get("ai_summary", "No overall summary could be generated."))

        st.subheader("Analysis by Category")
        for category in result.get("categories", []):
            cat_name = category.get('category', 'Unnamed')
            cat_risk = category.get('category_risk', 'Low')
            risk_color = "red" if cat_risk == "High" else "orange" if cat_risk == "Medium" else "green"

            st.markdown(
                f"<h3 style='color: {risk_color};'>{cat_name} (Overall Risk: {cat_risk})</h3>",
                unsafe_allow_html=True
            )
            st.write(f"**AI Summary:** {category.get('category_summary', 'N/A')}")
            
            with st.expander("Show Key Clauses..."):
                bullets = category.get("bullets", [])
                if not bullets:
                    st.write("No specific clauses were flagged in this category.")
                for bullet in bullets:
                    b_risk = bullet.get('risk', 'Low')
                    b_risk_color = "red" if b_risk == "High" else "orange" if b_risk == "Medium" else "grey"
                    
                    st.markdown(f"**- ({b_risk} Risk):** {bullet.get('text')}")
                    st.markdown(
                        f"<small style='color: #888;'>📍 Location: {bullet['provenance'].get('location', 'Unknown')} | "
                        f"🤔 Triggers: `{', '.join(bullet.get('rationale', []))}`</small>",
                        unsafe_allow_html=True
                    )
                    st.write("") # Spacer

    with tabs[1]:
        st.subheader("Search Full Text")
        search_query = st.text_input("Enter keyword to find in the original text")
        if search_query:
            # Simple search through the raw text
            matches = [line for line in result.get("raw_text", "").split('\n') if search_query.lower() in line.lower()]
            st.markdown(f"**Found {len(matches)} matching lines.**")
            st.code("\n".join(matches), language=None)

    with tabs[2]:
        st.subheader("Download Report")
        report_text = _format_analysis_for_export(result)
        st.download_button(
            "Download Analysis as Text File",
            data=report_text,
            file_name="analysis_summary.txt",
            mime="text/plain"
        )
else:
    st.info("Paste text or upload a document, then click **Run Analyzer**.")
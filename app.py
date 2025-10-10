"""
Streamlit frontend for Terms & Conditions Analyzer (v1.2 Final).
- Adds trigger highlighting in UI and PDF for better readability.
- Uses updated pipeline with improved summary prompts.
"""
import io
import json
import re
import sqlite3
from typing import Dict, Any, List
import streamlit as st

try:
    import pdfplumber
except Exception: pdfplumber = None
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.colors import red, orange, grey
except Exception: SimpleDocTemplate = None

from pipeline import process_document
from config import DEFAULT_KEYWORDS

# ---------------- Helper Functions ---------------- #
def _extract_text_from_pdf(file_bytes: bytes) -> Dict[int, str]:
    if not pdfplumber:
        st.error("`pdfplumber` is not installed. Please run `pip install pdfplumber`.")
        return {}
    pages = {}
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip(): pages[i] = text
    return pages

def _highlight_triggers(text: str, triggers: List[str], is_pdf: bool = False) -> str:
    """✅ Helper function to highlight trigger keywords in text."""
    # Sort triggers by length, longest first, to avoid partial matches (e.g., matching "share" before "share data")
    sorted_triggers = sorted(triggers, key=len, reverse=True)
    for trigger in sorted_triggers:
        # Use regex to find whole words to avoid matching parts of words
        pattern = re.compile(f"\\b({re.escape(trigger)})\\b", re.IGNORECASE)
        if is_pdf:
            text = pattern.sub(r"<b>\1</b>", text)
        else:
            text = pattern.sub(r"`\1`", text) # Use markdown code formatting for highlighting
    return text

def _format_analysis_for_pdf(result: Dict[str, Any]) -> bytes:
    if not SimpleDocTemplate:
        st.error("ReportLab not installed. PDF export disabled.")
        return b""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("<b>Terms & Conditions Analysis Report</b>", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("<b>Overall AI Summary</b>", styles["Heading2"]))
    story.append(Paragraph(result.get("ai_summary", "N/A"), styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    for cat in result.get("categories", []):
        story.append(Paragraph(f"{cat.get('category')} (Risk: {cat.get('category_risk')})", styles["Heading3"]))
        story.append(Paragraph(cat.get("category_summary", "No summary available."), styles["Normal"]))
        story.append(Spacer(1, 0.1 * inch))
        for bullet in cat.get("bullets", []):
            # ✅ Highlight triggers in the PDF text
            highlighted_text = _highlight_triggers(bullet.get('text'), bullet.get('rationale', []), is_pdf=True)
            text = f"- ({bullet.get('risk')}) {highlighted_text}"
            story.append(Paragraph(text, styles["Normal"]))
            loc = bullet["provenance"].get("location", "Unknown")
            story.append(Paragraph(f"<font size=8 color='grey'>📍 Location: {loc}</font>", styles["Normal"]))
            story.append(Spacer(1, 0.05 * inch))
        story.append(Spacer(1, 0.2 * inch))
    doc.build(story)
    return buffer.getvalue()

# (Database functions and UI setup are unchanged)
def init_db():
    conn = sqlite3.connect("analyses.db")
    conn.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, doc_type TEXT, summary_json TEXT)")
    conn.commit()
    return conn

st.set_page_config(page_title="Terms Analyzer", page_icon="⚖️", layout="wide")
st.title("⚖️ Terms & Conditions Analyzer")
# (Sidebar UI is unchanged)
with st.sidebar:
    st.header("Settings")
    selected_set = st.selectbox("Document Type", ["Software ToS"])
    st.write("---")
    st.subheader("Past Analyses")
    conn = init_db()
    past = conn.execute("SELECT id, doc_type FROM documents ORDER BY id DESC").fetchall()
    if past:
        for doc_id, doc_type in past:
            if st.button(f"Load {doc_type} #{doc_id}"):
                row = conn.execute("SELECT summary_json FROM documents WHERE id=?", (doc_id,)).fetchone()
                st.session_state["result"] = json.loads(row[0]) if row else None

# (Input section is unchanged)
st.header("📥 Input Document")
pasted = st.text_area("Paste text here", height=250)
uploaded_pdf = st.file_uploader("Or upload a PDF", type=["pdf"])
run_btn = st.button("▶ Run Analyzer")

text_pages = {}
if uploaded_pdf: text_pages = _extract_text_from_pdf(uploaded_pdf.getvalue())
elif pasted.strip(): text_pages = {1: pasted.strip()}

if run_btn:
    if not text_pages: st.warning("Please provide text or upload a PDF.")
    else:
        with st.spinner("Analyzing document..."):
            config = {"keywords": DEFAULT_KEYWORDS}
            data = process_document(text_pages, config)
            st.session_state["result"] = data
            conn.execute("INSERT INTO documents (doc_type, summary_json) VALUES (?, ?)", (selected_set, json.dumps(data)))
            conn.commit()

result = st.session_state.get("result")
if result:
    tabs = st.tabs(["📊 Summary", "📄 Clauses/Search", "📥 Export"])
    with tabs[0]:
        st.subheader("Overall AI Summary")
        st.info(result.get("ai_summary"))
        st.subheader("Analysis by Category")
        for category in result.get("categories", []):
            cat_risk = category.get("category_risk", "Low")
            color = {"High": "red", "Medium": "orange", "Low": "green"}.get(cat_risk, "gray")
            st.markdown(f"<h3 style='color:{color}'>{category.get('category')} (Risk: {cat_risk})</h3>", unsafe_allow_html=True)
            st.write(f"**Summary:** {category.get('category_summary')}")
            with st.expander("Show Key Clauses..."):
                for bullet in category.get("bullets", []):
                    # ✅ Highlight triggers in the Streamlit UI
                    highlighted_text = _highlight_triggers(bullet.get('text'), bullet.get('rationale', []))
                    st.markdown(f"**- ({bullet.get('risk')} Risk):** {highlighted_text}")
                    st.markdown(f"<small style='color:#888'>📍 {bullet['provenance'].get('location')}</small>", unsafe_allow_html=True)

    # (Search and Export tabs are functionally unchanged, but use the new functions)
    with tabs[1]:
        st.subheader("Search Full Text")
        query = st.text_input("Enter keyword to search in full text")
        if query:
            cleaned_text = result.get("raw_text", "")
            matches = [line for line in cleaned_text.split('\n') if query.lower() in line.lower()]
            st.markdown(f"**Found {len(matches)} matches.**")
            st.code("\n".join(matches))
    with tabs[2]:
        st.subheader("Download Full PDF Report")
        pdf_data = _format_analysis_for_pdf(result)
        st.download_button("📥 Download Report", data=pdf_data, file_name="terms_full_report.pdf", mime="application/pdf")
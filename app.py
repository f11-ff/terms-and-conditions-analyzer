"""
Streamlit frontend for Terms & Conditions Analyzer (v1.1 Final).
- Replaced PyPDF2 with pdfplumber for superior text extraction (fixes spacing).
- Uses updated pipeline to ensure all clauses show triggers.
"""
import io
import json
import sqlite3
from typing import Dict, Any
import streamlit as st

# ✅ Replaced PDF library
try:
    import pdfplumber
except Exception: pdfplumber = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except Exception: SimpleDocTemplate = None

from pipeline import process_document
from config import DEFAULT_KEYWORDS

# ---------------- PDF Extraction (Upgraded) ---------------- #
def _extract_text_from_pdf(file_bytes: bytes) -> Dict[int, str]:
    """✅ Extracts clean text from a PDF using pdfplumber."""
    if not pdfplumber:
        st.error("`pdfplumber` is not installed. Please run `pip install pdfplumber`.")
        return {}
    
    pages = {}
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages[i] = text
    return pages

# (The rest of the app.py file is unchanged but included for completeness)
# ---------------- PDF Export ---------------- #
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
            text = f"- ({bullet.get('risk')}) {bullet.get('text')}"
            story.append(Paragraph(text, styles["Normal"]))
            loc = bullet["provenance"].get("location", "Unknown")
            triggers = ", ".join(bullet.get("rationale", []))
            details_text = f"<font size=8 color='grey'>📍 {loc} | 🤔 Triggers: {triggers}</font>"
            story.append(Paragraph(details_text, styles["Normal"]))
            story.append(Spacer(1, 0.05 * inch))
        story.append(Spacer(1, 0.2 * inch))
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# ---------------- Database ---------------- #
def init_db():
    conn = sqlite3.connect("analyses.db")
    conn.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, doc_type TEXT, summary_json TEXT)")
    conn.commit()
    return conn

# ---------------- UI ---------------- #
st.set_page_config(page_title="Terms Analyzer", page_icon="⚖️", layout="wide")
st.title("⚖️ Terms & Conditions Analyzer")

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
                    st.markdown(f"**- ({bullet.get('risk')} Risk):** {bullet.get('text')}")
                    st.markdown(f"<small style='color:#888'>📍 {bullet['provenance'].get('location')} | 🤔 Triggers: `{', '.join(bullet.get('rationale', []))}`</small>", unsafe_allow_html=True)
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
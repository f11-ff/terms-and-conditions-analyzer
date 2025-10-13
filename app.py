# app.py

"""
Streamlit frontend for Terms & Conditions Analyzer (v1.9 – Privacy Fix).
- Removed the shared database and "Past Analyses" feature to ensure user privacy.
"""
import io
import json
import re
from typing import Dict, Any, List
import streamlit as st
import requests
import pandas as pd

# Import from other project files
from pipeline import process_document
from config import DEFAULT_KEYWORDS, RISK_SCORES
from legal_jargon import JARGON_TERMS

# Attempt to import optional libraries
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:
    SimpleDocTemplate = None

# ---------------- App Configuration ---------------- #
CATEGORY_SETS = {
    "Software ToS": [
        "Data Collection", "Data Sharing", "User Rights", "Restrictions", "Termination", "Refunds & Billing", 
        "Dispute Resolution", "Liability & Warranty", "User Content Ownership", "Third-party Integration", "Security & Breach Responsibility"
    ],
    "Rental / Lease Agreement": ["Lease Terms & Duration", "Financials (Rent, Fees, Deposit)", "Responsibilities & Rules", "Lease Termination"],
    "Insurance Policy": ["Coverage & Limits", "Exclusions (What's Not Covered)", "Premiums & Payments", "Claims & Procedures"],
    "Loan Agreement": ["Loan Terms (Principal, Interest)", "Repayment Schedule", "Fees & Penalties", "Collateral & Default"],
}

# ---------------- Helper Functions ---------------- #
def _extract_text_from_pdf(file_bytes: bytes) -> Dict[int, str]:
    if not pdfplumber:
        st.error("`pdfplumber` is not installed. PDF processing is disabled.")
        return {}
    pages = {}
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages[i] = text
    return pages

# (Other helper functions like _highlight_triggers, get_online_definition, _format_analysis_for_pdf are unchanged)
def _highlight_triggers(text: str, triggers: List[str]) -> str:
    sorted_triggers = sorted(triggers, key=len, reverse=True)
    for trigger in sorted_triggers:
        pattern = re.compile(f"\\b({re.escape(trigger)})\\b", re.IGNORECASE)
        text = pattern.sub(r"`\1`", text)
    return text

def get_online_definition(word: str) -> str:
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        response.raise_for_status()
        data = response.json()
        first_meaning = data[0]['meanings'][0]['definitions'][0]
        definition = first_meaning.get('definition', 'No definition found.')
        example = first_meaning.get('example')
        result = f"**Definition:** {definition}"
        if example:
            result += f"\n\n**Example:** *{example}*"
        return result
    except requests.exceptions.HTTPError:
        return f"Could not find a definition for **{word}**. Please check the spelling."
    except Exception:
        return "An error occurred during lookup. Please check your internet connection."

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
            details_text = f"<font size=8 color='grey'>📍 Location: {loc} | 🤔 Triggers: {triggers}</font>"
            story.append(Paragraph(details_text, styles["Normal"]))
            story.append(Spacer(1, 0.05 * inch))
        story.append(Spacer(1, 0.2 * inch))
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def display_risk_gauge(score: float):
    if score > 66:
        level, color, emoji = "High Risk", "#ff4b4b", "🚨"
    elif score > 33:
        level, color, emoji = "Moderate Risk", "#ffc400", "⚠️"
    else:
        level, color, emoji = "Low Risk", "#28a745", "✅"
    st.markdown(
        f"""
        <div style="background-color: #262730; border: 1px solid {color}; border-radius: 7px; padding: 15px; text-align: center;">
            <span style="font-size: 1.2em;">{emoji} Document Risk Level</span>
            <h2 style="color: {color}; margin: 5px 0 0 0;">{level}</h2>
            <small>Based on a weighted analysis of flagged clauses.</small>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- ❌ Database functions are now removed to ensure privacy ---

# ---------------- UI ---------------- #
st.set_page_config(page_title="Terms Analyzer", page_icon="⚖️", layout="wide")
st.title("⚖️ Terms & Conditions Analyzer")

if 'keywords' not in st.session_state:
    st.session_state.keywords = DEFAULT_KEYWORDS
if 'risk_scores' not in st.session_state:
    st.session_state.risk_scores = RISK_SCORES

with st.sidebar:
    st.header("Settings")
    selected_set = st.selectbox("Document Type", list(CATEGORY_SETS.keys()))
    
    st.write("---")
    st.subheader("🔍 Word Lookup")
    word_to_define = st.text_input("Enter a word to define:")
    if st.button("Define"):
        if word_to_define:
            with st.spinner(f"Defining '{word_to_define}'..."):
                definition = get_online_definition(word_to_define)
                st.markdown(definition)
        else:
            st.warning("Please enter a word.")
    
    # --- ❌ "Past Analyses" section is removed from the sidebar ---

st.header("📥 Input Document")
pasted = st.text_area("Paste text here", height=250)
uploaded_pdf = st.file_uploader("Or upload a PDF", type=["pdf"])
run_btn = st.button("▶ Run Analyzer")

text_pages = {}
if uploaded_pdf:
    text_pages = _extract_text_from_pdf(uploaded_pdf.getvalue())
elif pasted.strip():
    text_pages = {1: pasted.strip()}

if run_btn:
    if not text_pages:
        st.warning("Please provide text or upload a PDF.")
    else:
        with st.spinner("Analyzing document..."):
            required_categories = CATEGORY_SETS[selected_set]
            config = {
                "keywords": {cat: st.session_state.keywords.get(cat, []) for cat in required_categories},
                "categories": required_categories,
                "risk_scores": st.session_state.risk_scores
            }
            data = process_document(text_pages, config)
            st.session_state["result"] = data
            # --- ❌ The line that saved the analysis to the database is removed ---

result = st.session_state.get("result")
if result:
    tabs = st.tabs(["📊 Summary", "⚙️ Configuration", "📥 Export"])
    
    with tabs[0]:
        st.subheader("Document Risk Assessment")
        display_risk_gauge(result.get("overall_risk_score", 0))
        st.markdown("<br>", unsafe_allow_html=True)
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
                    clause_text = bullet.get('text', '')
                    triggers = bullet.get('rationale', [])
                    highlighted_text = _highlight_triggers(clause_text, triggers)
                    st.markdown(f"**- ({bullet.get('risk')} Risk):** {highlighted_text}", unsafe_allow_html=True)
                    st.markdown(f"<small style='color:#888'>📍 {bullet['provenance'].get('location')}</small>", unsafe_allow_html=True)
                    found_jargon = [term for term in JARGON_TERMS if re.search(f"\\b{term}\\b", clause_text, re.IGNORECASE)]
                    if found_jargon:
                        cols = st.columns(len(found_jargon) + 4)
                        for i, term in enumerate(found_jargon):
                            with cols[i]:
                                with st.popover(f"_{term.title()}_"):
                                    st.markdown(JARGON_TERMS[term])
                    st.markdown("---")

    with tabs[1]:
        st.subheader("Session Configuration Editor")
        st.warning("Changes made here only apply to the current session. To load permanent changes from your files, use the 'Reload' button.")
        if st.button("🔄 Reload Default Config from File"):
            st.session_state.keywords = DEFAULT_KEYWORDS
            st.session_state.risk_scores = RISK_SCORES
            st.success("Default configuration has been reloaded!")
        st.markdown("---")
        st.markdown("#### Risk Scores")
        risk_scores_text = st.text_area("Risk Scores (JSON)", value=json.dumps(st.session_state.risk_scores, indent=2), height=250)
        st.markdown("#### Category Keywords")
        keywords_text = st.text_area("Category Keywords (JSON)", value=json.dumps(st.session_state.keywords, indent=2), height=400)
        if st.button("Apply Configuration Changes"):
            try:
                st.session_state.risk_scores = json.loads(risk_scores_text)
                st.session_state.keywords = json.loads(keywords_text)
                st.success("Configuration updated for this session! Run the analyzer again to see the new results.")
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your syntax.")

    with tabs[2]:
        st.subheader("Download Full PDF Report")
        pdf_data = _format_analysis_for_pdf(result)
        st.download_button("📥 Download Report", data=pdf_data, file_name="terms_full_report.pdf", mime="application/pdf")
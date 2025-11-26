import streamlit as st
from dotenv import load_dotenv
import os
from utils.similarity import calculate_similarity, similarity_details

from openai import OpenAI
import plotly.graph_objects as go
import pdfplumber
import docx
import requests
from bs4 import BeautifulSoup
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ---------------- ENV + OPENAI ----------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# ---------------- File Extractors ----------------
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_txt(file):
    return file.read().decode("utf-8")

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=" ")
        return " ".join(text.split())
    except:
        return ""

# ---------------- Gauge Chart ----------------
def draw_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Plagiarism Percentage"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 25], 'color': "lightgreen"},
                {'range': [25, 50], 'color': "yellow"},
                {'range': [50, 75], 'color': "orange"},
                {'range': [75, 100], 'color': "red"},
            ],
        }
    ))
    fig.update_layout(height=300)
    return fig

# ---------------- LLM Explanation ----------------
def explain_similarity(student, reference):
    prompt = f"""
    Compare the following texts and explain the similarity clearly:

    Student Text: {student}
    Reference Text: {reference}

    Explain:
    - Whether it's copied or paraphrased
    - Which ideas match
    - Why similarity exists
    - How to rewrite more originally
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ---------------- PDF Report Generator ----------------
def generate_pdf(student, reference, score, explanation):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate("plagiarism_report.pdf", pagesize=letter)
    story = []

    story.append(Paragraph("<b>AI Plagiarism Checker Report</b>", styles["Title"]))
    story.append(Paragraph(f"<b>Plagiarism Score:</b> {score:.2f}%", styles["Normal"]))
    story.append(Paragraph("<b>Student Text:</b>", styles["Heading2"]))
    story.append(Paragraph(student, styles["Normal"]))
    story.append(Paragraph("<b>Reference Text:</b>", styles["Heading2"]))
    story.append(Paragraph(reference, styles["Normal"]))
    story.append(Paragraph("<b>AI Explanation:</b>", styles["Heading2"]))
    story.append(Paragraph(explanation, styles["Normal"]))

    doc.build(story)

    return "plagiarism_report.pdf"

# ---------------- DASHBOARD UI ----------------
st.set_page_config(page_title="AI Plagiarism Checker", layout="wide")

# -------- SIDEBAR BRANDING --------
st.sidebar.title("📘 AI Plagiarism Checker")
st.sidebar.markdown("Developed for Generative AI Project")
st.sidebar.markdown("By: **Sivanand**")
st.sidebar.markdown("---")

# -------- CUSTOM CSS --------
st.markdown("""
<style>
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -------- PAGE TITLE --------
st.title("📊 AI Plagiarism Detection Dashboard")
st.markdown("#### Upload any file (PDF / TXT / DOCX) or enter text/website URL")

col1, col2 = st.columns(2)

# ---------------- STUDENT INPUT ----------------
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📝 Student Text Input")
    student_method = st.selectbox(
        "Select Input Method (Student):",
        ["Enter Text", "Upload PDF", "Upload TXT", "Upload DOCX", "Website URL"],
        key="student"
    )

    student_text = ""

    if student_method == "Enter Text":
        student_text = st.text_area("Enter Student Text")

    elif student_method == "Upload PDF":
        up = st.file_uploader("Upload PDF", type=["pdf"], key="student_pdf")
        if up:
            student_text = extract_text_from_pdf(up)

    elif student_method == "Upload TXT":
        up = st.file_uploader("Upload TXT", type=["txt"], key="student_txt")
        if up:
            student_text = extract_text_from_txt(up)

    elif student_method == "Upload DOCX":
        up = st.file_uploader("Upload DOCX", type=["docx"], key="student_docx")
        if up:
            student_text = extract_text_from_docx(up)

    elif student_method == "Website URL":
        url = st.text_input("Enter Website URL", key="student_url")
        if url:
            student_text = extract_text_from_website(url)

    if student_text:
        st.markdown("### 🔍 Extracted Student Text Preview")
        st.write(student_text[:500] + "...")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- REFERENCE INPUT ----------------
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📚 Reference Text Input")
    ref_method = st.selectbox(
        "Select Input Method (Reference):",
        ["Enter Text", "Upload PDF", "Upload TXT", "Upload DOCX", "Website URL"],
        key="reference"
    )

    reference_text = ""

    if ref_method == "Enter Text":
        reference_text = st.text_area("Enter Reference Text")

    elif ref_method == "Upload PDF":
        up = st.file_uploader("Upload PDF", type=["pdf"], key="ref_pdf")
        if up:
            reference_text = extract_text_from_pdf(up)

    elif ref_method == "Upload TXT":
        up = st.file_uploader("Upload TXT", type=["txt"], key="ref_txt")
        if up:
            reference_text = extract_text_from_txt(up)

    elif ref_method == "Upload DOCX":
        up = st.file_uploader("Upload DOCX", type=["docx"], key="ref_docx")
        if up:
            reference_text = extract_text_from_docx(up)

    elif ref_method == "Website URL":
        url = st.text_input("Enter Website URL", key="ref_url")
        if url:
            reference_text = extract_text_from_website(url)

    if reference_text:
        st.markdown("### 🔍 Extracted Reference Text Preview")
        st.write(reference_text[:500] + "...")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RUN CHECK ----------------
st.markdown("---")

if st.button("🚀 Run Plagiarism Check"):
    if not student_text.strip() or not reference_text.strip():
        st.warning("⚠️ Both student and reference inputs are required!")
    else:
        score = calculate_similarity(student_text, reference_text)

        st.subheader("📊 Plagiarism Score")
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.plotly_chart(draw_gauge(score), use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("🔎 Sentence Similarity (>70%)")
        matches = similarity_details(student_text, reference_text)

        if len(matches) == 0:
            st.success("✔ No highly similar sentences found.")
        else:
            for s, r, sc in matches:
                st.info(f"**Student:** {s}\n\n**Reference:** {r}\n\n**Similarity:** {sc:.2f}%")
                st.write("---")

        st.subheader("🤖 AI Explanation")
        explanation = explain_similarity(student_text, reference_text)
        st.write(explanation)

        # PDF Download
        pdf_path = generate_pdf(student_text, reference_text, score, explanation)
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download Full Report (PDF)", f, file_name="plagiarism_report.pdf")

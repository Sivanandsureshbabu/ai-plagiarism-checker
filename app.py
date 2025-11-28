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
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': "Plagiarism Percentage"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#4285F4"},
                'steps': [
                    {'range': [0, 25], 'color': "#C8E6C9"},
                    {'range': [25, 50], 'color': "#FFF9C4"},
                    {'range': [50, 75], 'color': "#FFE0B2"},
                    {'range': [75, 100], 'color': "#FFCDD2"},
                ],
            }
        )
    )
    fig.update_layout(height=300)
    return fig


# ---------------- LLM Explanation ----------------
def explain_similarity(student, reference):
    prompt = f"""
    Compare the following texts for plagiarism:

    Student Text: {student}
    Reference Text: {reference}

    Explain:
    - If it is copied or paraphrased
    - Which ideas match
    - Why similarity exists
    - How to rewrite more originally
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# ---------------- AI Generated Text Detector ----------------
def detect_ai_generated(text):
    prompt = f"""
    Analyze the following text and determine if it is AI-generated or human-written.

    Text:
    {text}

    Respond with:
    - AI-generated or Human-written
    - Confidence Level (High / Medium / Low)
    - Clear reason for your decision
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


# ---------------- CUSTOM UI CSS ----------------
st.markdown("""
<style>
:root {
    --primary: #1A73E8;
    --primary-hover: #1669c1;
    --text-dark: #202124;
    --text-light: #5f6368;
    --border: #dadce0;
}

[data-testid="stAppViewContainer"] {
    background: #f5f5f5;
}

.card {
    background: #ffffff;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    margin-bottom: 25px;
}

.stButton > button {
    background-color: #E3F2FD !important;
    color: #1A73E8 !important;
    padding: 10px 18px !important;
    border-radius: 8px !important;
    border: 1px solid #90CAF9 !important;
    font-size: 16px !important;
}

.stButton > button:hover {
    background-color: #BBDEFB !important;
    color: #0F5CC2 !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------- PAGE TITLE ----------------
st.title("📊 Plagiarism Checker")
st.markdown("#### Check plagiarism using multiple file types or website links.")


# ---------------- COLUMNS ----------------
col1, col2 = st.columns(2)


# ---------------- STUDENT INPUT ----------------
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📝 Student Input")

    student_method = st.selectbox(
        "Select Student Input Type",
        ["Enter Text", "Upload PDF", "Upload TXT", "Upload DOCX", "Website URL"],
        key="student"
    )

    student_text = ""

    if student_method == "Enter Text":
        student_text = st.text_area("Enter Student Text")

    elif student_method == "Upload PDF":
        file = st.file_uploader("Upload Student PDF", type=["pdf"])
        if file:
            student_text = extract_text_from_pdf(file)

    elif student_method == "Upload TXT":
        file = st.file_uploader("Upload TXT", type=["txt"])
        if file:
            student_text = extract_text_from_txt(file)

    elif student_method == "Upload DOCX":
        file = st.file_uploader("Upload DOCX", type=["docx"])
        if file:
            student_text = extract_text_from_docx(file)

    elif student_method == "Website URL":
        url = st.text_input("Enter Student Website URL")
        if url:
            student_text = extract_text_from_website(url)

    if student_text:
        st.markdown("### 🔍 Preview")
        st.write(student_text[:500] + "...")

        # AI GENERATED TEXT CHECKER
        st.markdown("### 🤖 AI-Generated Text Check")
        if st.button("Detect AI-Generated Text"):
            ai_result = detect_ai_generated(student_text)
            st.info(ai_result)

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- REFERENCE INPUT ----------------
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📚 Reference Input")

    ref_method = st.selectbox(
        "Select Reference Input Type",
        ["Enter Text", "Upload PDF", "Upload TXT", "Upload DOCX", "Website URL"],
        key="reference"
    )

    reference_text = ""

    if ref_method == "Enter Text":
        reference_text = st.text_area("Enter Reference Text")

    elif ref_method == "Upload PDF":
        file = st.file_uploader("Upload Reference PDF", type=["pdf"])
        if file:
            reference_text = extract_text_from_pdf(file)

    elif ref_method == "Upload TXT":
        file = st.file_uploader("Upload Reference TXT", type=["txt"])
        if file:
            reference_text = extract_text_from_txt(file)

    elif ref_method == "Upload DOCX":
        file = st.file_uploader("Upload Reference DOCX", type=["docx"])
        if file:
            reference_text = extract_text_from_docx(file)

    elif ref_method == "Website URL":
        url = st.text_input("Enter Reference Website URL")
        if url:
            reference_text = extract_text_from_website(url)

    if reference_text:
        st.markdown("### 🔍 Preview")
        st.write(reference_text[:500] + "...")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------- RUN CHECK ----------------
st.markdown("---")

if st.button("🚀 Run Plagiarism Check"):
    if not student_text.strip() or not reference_text.strip():
        st.warning("⚠️ Both fields cannot be empty!")
    else:
        score = calculate_similarity(student_text, reference_text)

        st.subheader("📊 Plagiarism Score")
        st.plotly_chart(draw_gauge(score), use_container_width=False)

        st.subheader("🔎 Similar Sentences (>70%)")
        matches = similarity_details(student_text, reference_text)

        if not matches:
            st.success("✔ No major similarities found!")
        else:
            for s, r, sc in matches:
                st.info(f"**Student:** {s}\n\n**Reference:** {r}\n\n**Match:** {sc:.2f}%")
                st.write("---")

        st.subheader("🤖 AI Explanation")
        explanation = explain_similarity(student_text, reference_text)
        st.write(explanation)

        pdf_path = generate_pdf(student_text, reference_text, score, explanation)

        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download Full Report (PDF)", f, file_name="plagiarism_report.pdf")

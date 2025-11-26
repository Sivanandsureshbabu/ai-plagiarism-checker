from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

from utils.similarity import calculate_similarity, similarity_details
from openai import OpenAI

client = OpenAI(api_key=api_key)

def generate_explanation(student, reference):
    prompt = f"""
    Compare the following two texts and explain the similarity:

    Student Text: {student}
    Reference Text: {reference}

    Provide:
    - Whether it's copied or paraphrased
    - Why they are similar
    - Which ideas match
    - How to rewrite more originally
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


# -------- MAIN PROGRAM --------

student_text = input("\nEnter Student Text:\n")
reference_text = input("\nEnter Reference Text:\n")

# Overall plagiarism
score = calculate_similarity(student_text, reference_text)
print(f"\n📌 Overall Plagiarism Score: {score:.2f}%")

# Sentence-level matching
print("\n🔎 Sentence-Level Matches (>70%):\n")
matches = similarity_details(student_text, reference_text)

for s, r, sc in matches:
    print(f"Student: {s}")
    print(f"Reference: {r}")
    print(f"Similarity: {sc:.2f}%\n")

# LLM explanation
print("\n🤖 AI Explanation:\n")
print(generate_explanation(student_text, reference_text))

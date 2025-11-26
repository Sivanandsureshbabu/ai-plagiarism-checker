from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.text_processing import split_into_sentences

def calculate_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
    return score * 100

def similarity_details(text1, text2, threshold=0.70):
    student_sentences = split_into_sentences(text1)
    reference_sentences = split_into_sentences(text2)

    results = []

    for s in student_sentences:
        for r in reference_sentences:
            vectorizer = TfidfVectorizer().fit_transform([s, r])
            vectors = vectorizer.toarray()
            score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]

            if score >= threshold:
                results.append((s, r, score * 100))

    return results

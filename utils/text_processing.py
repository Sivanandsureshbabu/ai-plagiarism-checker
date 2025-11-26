import nltk
nltk.download('punkt', quiet=True)

def split_into_sentences(text):
    return nltk.sent_tokenize(text)

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

model = SentenceTransformer("all-MiniLM-L6-v2")


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were",
    "do", "does", "did", "what", "how", "many",
    "can", "to", "of", "for", "in", "on", "and",
    "or", "this", "that", "employees", "employee"
}


def get_keywords(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    return set(word for word in words if word not in STOPWORDS)


def evaluate_retrieval(question, context):

    # Semantic similarity
    question_embedding = model.encode([question])
    context_embedding = model.encode([context])

    semantic_score = cosine_similarity(
        question_embedding,
        context_embedding
    )[0][0]

    semantic_score = float((semantic_score + 1) / 2)

    # Keyword/topic overlap
    question_keywords = get_keywords(question)
    context_keywords = get_keywords(context)

    if question_keywords:
        keyword_score = len(
            question_keywords.intersection(context_keywords)
        ) / len(question_keywords)
    else:
        keyword_score = 0.0

    # Combined score
    score = (
        0.6 * semantic_score +
        0.4 * keyword_score
    )

    score = round(score, 2)

    if score >= 0.75:
        decision = "SUFFICIENT"
    else:
        decision = "INSUFFICIENT"

    return score, decision
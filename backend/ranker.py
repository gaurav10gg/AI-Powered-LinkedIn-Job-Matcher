from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def rank_posts(resume_text, posts, top_k=5):
    """
    Ranks LinkedIn posts based on similarity to resume text.
    """

    documents = [resume_text] + [post["content"] for post in posts]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    resume_vector = tfidf_matrix[0]
    post_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(resume_vector, post_vectors)[0]

    ranked_results = []

    for idx, score in enumerate(similarities):
        ranked_results.append({
            "author": posts[idx]["author"],
            "content": posts[idx]["content"],
            "links": posts[idx].get("links", []),
            "score": round(float(score), 3)
        })

    ranked_results.sort(key=lambda x: x["score"], reverse=True)

    return ranked_results[:top_k]

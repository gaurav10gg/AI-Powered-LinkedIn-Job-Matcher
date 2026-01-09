import spacy
from collections import Counter


nlp = spacy.load("en_core_web_sm")


TECH_SKILLS = {
    "python", "java", "javascript", "c", "sql",
    "react", "react.js", "next.js",
    "node", "node.js", "express", "mongodb",
    "machine learning", "deep learning",
    "data science", "artificial intelligence",
    "ai", "ml",
    "git", "github",
    "docker", "aws"
}

def extract_skills_and_topics(resume_text: str, top_k: int = 15):
    doc = nlp(resume_text)

    phrases = []

    for chunk in doc.noun_chunks:
        phrase = chunk.text.lower().strip()
        if len(phrase) > 2:
            phrases.append(phrase)

    
    for token in doc:
        if token.text.lower() in TECH_SKILLS:
            phrases.append(token.text.lower())

    freq = Counter(phrases)

    skills = []
    topics = []

    for phrase, _ in freq.most_common():
        if phrase in TECH_SKILLS:
            skills.append(phrase)
        elif any(word in phrase for word in ["ai", "ml", "analytics", "backend", "frontend", "full stack"]):
            topics.append(phrase)

    return {
        "skills": skills[:top_k],
        "topics": topics[:top_k]
    }



if __name__ == "__main__":
    from backend.resume_parser import extract_text_from_pdf

    resume_text = extract_text_from_pdf(
        "Gaurav-G-FlowCV-Resume-20251212.pdf"
    )

    extracted = extract_skills_and_topics(resume_text)

    print("\nSkills:")
    for s in extracted["skills"]:
        print("-", s)

    print("\nTopics:")
    for t in extracted["topics"]:
        print("-", t)

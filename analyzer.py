import pandas as pd
import os
import re
from collections import Counter
from PyPDF2 import PdfReader
import math

SKILL_FOLDER = "skills"


def clean(text):
    return re.sub(r'[^a-zA-Z\s]', ' ', text.lower())


def extract_text(file):
    file.seek(0)
    reader = PdfReader(file)
    text = ""
    for p in reader.pages:
        text += p.extract_text() or ""
    return text


def load_domains():
    domains = {}

    for f in os.listdir(SKILL_FOLDER):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(SKILL_FOLDER, f))
            col = df.columns[0]

            domains[f.replace(".csv", "")] = list(
                df[col].dropna().astype(str).str.lower()
            )

    return domains


def repetition(text):
    words = clean(text).split()
    count = Counter(words)
    return {w: c for w, c in count.items() if c > 3}


def nlp_jd_score(resume_text, jd_text):

    def vectorize(text):
        words = clean(text).split()
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return freq

    v1 = vectorize(resume_text)
    v2 = vectorize(jd_text)

    all_words = set(v1.keys()).union(set(v2.keys()))

    vec1 = [v1.get(w, 0) for w in all_words]
    vec2 = [v2.get(w, 0) for w in all_words]

    dot = sum(a*b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a*a for a in vec1))
    mag2 = math.sqrt(sum(b*b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 0

    return int((dot / (mag1 * mag2)) * 100)


def analyze_resume(file, jd_text):

    text = extract_text(file)
    cleaned = clean(text)

    domains = load_domains()

    scores = {
        d: sum(1 for s in skills if s in cleaned)
        for d, skills in domains.items()
    }

    resume_domain = max(scores, key=scores.get)

    jd_domain = "N/A"
    jd_clean = ""

    if jd_text:
        jd_clean = clean(jd_text)

        jd_scores = {
            d: sum(1 for s in skills if s in jd_clean)
            for d, skills in domains.items()
        }

        jd_domain = max(jd_scores, key=jd_scores.get)

    skills = domains[resume_domain]

    matched = [s for s in skills if s in cleaned]
    missing = [s for s in skills if s not in cleaned]

    score = int((len(matched) / len(skills)) * 100) if skills else 0

    jd_score = nlp_jd_score(text, jd_text) if jd_text else 0

    return {
        "resume_domain": resume_domain,
        "jd_domain": jd_domain,
        "matched": matched,
        "missing": missing,
        "score": score,
        "jd_score": jd_score,
        "repeated": repetition(text)
    }
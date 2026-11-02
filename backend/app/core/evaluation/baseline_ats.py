"""Baseline Mini-ATS — traditional keyword-based matching using TF-IDF."""

from typing import Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class BaselineATS:
    """Traditional legacy ATS that ranks resumes using keyword frequency and TF-IDF."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            lowercase=True,
        )

    def rank_candidates(
        self,
        job_description: str,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Rank candidates against JD using TF-IDF cosine similarity."""
        if not candidates or not job_description:
            return []

        doc_texts = [c.get("raw_text", "") for c in candidates]
        all_texts = [job_description] + doc_texts

        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        jd_vector = tfidf_matrix[0:1]
        cand_vectors = tfidf_matrix[1:]

        # Compute cosine similarity
        similarities = (cand_vectors * jd_vector.T).toarray().flatten()

        results = []
        for idx, c in enumerate(candidates):
            results.append({
                "candidate_id": c.get("id", f"cand-{idx+1}"),
                "name": c.get("name", f"Candidate {idx+1}"),
                "score": float(similarities[idx]),
                "ground_truth_relevance": c.get("ground_truth_relevance", 0),
                "is_keyword_trap": c.get("is_keyword_trap", False),
            })

        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        for rank_idx, r in enumerate(results, start=1):
            r["rank"] = rank_idx

        return results

"""Stage 2 Cross-Encoder Reranker for top-K candidate and snippet reranking."""

import logging
from typing import Any
import numpy as np

from app.config import settings
from app.core.jd.ontology import ontology

logger = logging.getLogger("rankwise.embeddings.reranker")


class CrossEncoderReranker:
    """Stage 2 Cross-Encoder for precision reranking of top retrieved snippets."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.cross_encoder_model
        self._ce_model: Any = None

        try:
            from sentence_transformers import CrossEncoder
            self._ce_model = CrossEncoder(self.model_name)
            logger.info(f"Loaded CrossEncoder: {self.model_name}")
        except Exception as e:
            logger.info(f"CrossEncoder not active ({e}). Using semantic alignment reranker.")
            self._ce_model = None

    def predict_scores(self, query: str, texts: list[str]) -> list[float]:
        """Score (query, text) pairs using cross-encoder or semantic alignment fallback."""
        if not texts:
            return []

        if self._ce_model is not None:
            try:
                pairs = [(query, t) for t in texts]
                raw_scores = self._ce_model.predict(pairs)
                # Apply sigmoid if logits
                scores = 1.0 / (1.0 + np.exp(-np.array(raw_scores)))
                return [float(s) for s in scores]
            except Exception as e:
                logger.warning(f"CrossEncoder prediction failed: {e}. Falling back.")

        STOPWORDS = {
            "with", "in", "at", "to", "for", "of", "and", "a", "an", "the", "on", "is",
            "by", "as", "or", "from", "be", "have", "has", "had", "using", "used", "into",
            "experience", "production", "years", "knowledge", "skills", "ability", "proficient"
        }
        # Extract meaningful content terms
        import re
        q_tokens = [w.strip(".,;:()[]\"'") for w in re.findall(r"\b[a-zA-Z0-9_+#.-]+\b", query.lower())]
        query_terms = [w for w in q_tokens if len(w) > 2 and w not in STOPWORDS]

        scores = []
        for t in texts:
            t_lower = t.lower()
            t_tokens = [w.strip(".,;:()[]\"'") for w in re.findall(r"\b[a-zA-Z0-9_+#.-]+\b", t_lower)]
            doc_terms = set(w for w in t_tokens if len(w) > 2 and w not in STOPWORDS)

            if not query_terms:
                scores.append(0.1)
                continue

            # Exact keyword overlap ratio
            matched_terms = sum(1 for qt in query_terms if qt in doc_terms or any(qt in dt for dt in doc_terms))
            overlap = matched_terms / len(query_terms)

            # Ontology semantic similarity bonus
            ontology_bonus = 0.0
            for qt in query_terms:
                for dt in doc_terms:
                    sim = ontology.get_similarity(qt, dt)
                    if sim > ontology_bonus:
                        ontology_bonus = sim

            # Base score calculation: only give bonuses if there is actual topical match
            if overlap > 0 or ontology_bonus > 0.4:
                type_bonus = 0.15 if " at " in t else 0.08
                score = min(1.0, (overlap * 0.6) + (ontology_bonus * 0.3) + type_bonus)
            else:
                score = 0.0

            scores.append(round(score, 3))

        return scores

    def rerank(
        self, query: str, items: list[dict], text_key: str = "text", top_k: int = 5
    ) -> list[dict]:
        """Rerank a list of candidate items (chunks or candidates) by query relevance."""
        if not items:
            return []

        texts = [item.get(text_key, "") for item in items]
        scores = self.predict_scores(query, texts)

        for item, score in zip(items, scores, strict=False):
            item["rerank_score"] = score

        # Sort descending by rerank score
        sorted_items = sorted(items, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return sorted_items[:top_k]


# Singleton reranker instance
reranker = CrossEncoderReranker()

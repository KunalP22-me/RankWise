"""Bi-Encoder embedding model with vector caching and graceful offline semantic fallback."""

import hashlib
import logging
from typing import Any
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from app.config import settings
from app.core.jd.ontology import ontology

logger = logging.getLogger("rankwise.embeddings.encoder")

# In-memory vector cache: sha256(text) -> numpy array
_VECTOR_CACHE: dict[str, np.ndarray] = {}


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SemanticFallbackVectorizer:
    """Fixed-dimension semantic vectorizer using HashingVectorizer + ontology concept projection."""

    def __init__(self, n_features: int = 512):
        self.n_features = n_features
        self.vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            lowercase=True,
            ngram_range=(1, 2),
            stop_words="english",
        )

    def _expand_synonyms(self, text: str) -> str:
        """Enrich text with ontology synonyms and parent categories for semantic alignment."""
        tokens = [t.strip(".,;:()[]\"'") for t in text.lower().split()]
        additions = []
        for t in tokens:
            if not t:
                continue
            norm = ontology.normalize(t)
            if norm != t:
                additions.append(norm)
            parent = ontology.get_parent(norm)
            if parent:
                additions.append(parent)
                grandparent = ontology.get_parent(parent)
                if grandparent:
                    additions.append(grandparent)
        return text + " " + " ".join(additions)

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.n_features), dtype=np.float32)

        expanded = [self._expand_synonyms(t) for t in texts]
        matrix = self.vectorizer.transform(expanded).toarray().astype(np.float32)

        # Ensure unit L2 normalization
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms


class BiEncoder:
    """Bi-Encoder embedding engine supporting SentenceTransformers with vector caching."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.bi_encoder_model
        self._st_model: Any = None
        self._fallback = SemanticFallbackVectorizer()

        # Try loading sentence-transformers if available
        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded SentenceTransformer: {self.model_name}")
        except Exception as e:
            logger.info(f"SentenceTransformer not active ({e}). Using semantic fallback vectorizer.")
            self._st_model = None

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of text strings into normalized L2 embeddings."""
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        # Check cache
        cached_vectors = {}
        missing_texts = []
        missing_indices = []

        for idx, t in enumerate(texts):
            h = _hash_text(t)
            if h in _VECTOR_CACHE:
                cached_vectors[idx] = _VECTOR_CACHE[h]
            else:
                missing_texts.append(t)
                missing_indices.append(idx)

        new_vectors: np.ndarray | None = None
        if missing_texts:
            if self._st_model is not None:
                try:
                    new_vectors = self._st_model.encode(
                        missing_texts, normalize_embeddings=True, show_progress_bar=False
                    )
                except Exception as e:
                    logger.warning(f"SentenceTransformer encode failed: {e}. Using fallback.")
                    new_vectors = self._fallback.encode(missing_texts)
            else:
                new_vectors = self._fallback.encode(missing_texts)

            # Store in cache
            for m_idx, vec in zip(missing_indices, new_vectors, strict=False):
                h = _hash_text(texts[m_idx])
                _VECTOR_CACHE[h] = vec
                cached_vectors[m_idx] = vec

        # Reassemble in original order
        results = [cached_vectors[i] for i in range(len(texts))]
        return np.array(results, dtype=np.float32)

    @staticmethod
    def compute_similarity(embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> np.ndarray:
        """Compute cosine similarity matrix between two sets of normalized vectors."""
        # Both sets assumed L2 normalized: similarity is dot product
        return np.dot(embeddings_a, embeddings_b.T)


# Singleton bi-encoder instance
bi_encoder = BiEncoder()

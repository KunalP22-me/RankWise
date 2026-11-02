"""Two-stage semantic retrieval engine (Bi-Encoder Retrieval + Cross-Encoder Reranking)."""

import logging
from typing import Any

from app.core.embeddings.chunker import ResumeChunk
from app.core.embeddings.encoder import bi_encoder
from app.core.embeddings.reranker import reranker
from app.schemas.job import Requirement

logger = logging.getLogger("rankwise.embeddings.retriever")


class TwoStageRetriever:
    """Orchestrates bi-encoder retrieval followed by cross-encoder snippet reranking."""

    def __init__(self):
        self.encoder = bi_encoder
        self.reranker = reranker

    def match_requirements_to_chunks(
        self,
        chunks: list[ResumeChunk],
        requirements: list[Requirement],
        stage1_top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve and rerank the best supporting resume chunk for each job requirement.

        Returns a list of dicts:
        [
          {
            "requirement_text": str,
            "requirement_type": str,
            "best_chunk": ResumeChunk | None,
            "semantic_similarity": float,
            "rerank_score": float,
            "top_candidates": list[dict],
          }, ...
        ]
        """
        if not requirements or not chunks:
            return [
                {
                    "requirement_text": req.text,
                    "requirement_type": req.type,
                    "best_chunk": None,
                    "semantic_similarity": 0.0,
                    "rerank_score": 0.0,
                    "top_candidates": [],
                }
                for req in requirements
            ]

        # Stage 1: Embed requirement queries and resume chunks
        req_texts = [r.text for r in requirements]
        chunk_texts = [c.text for c in chunks]

        req_embeddings = self.encoder.encode(req_texts)
        chunk_embeddings = self.encoder.encode(chunk_texts)

        # Compute cosine similarity matrix: shape (num_requirements, num_chunks)
        sim_matrix = self.encoder.compute_similarity(req_embeddings, chunk_embeddings)

        results = []
        for r_idx, req in enumerate(requirements):
            sims = sim_matrix[r_idx]

            # Get indices of top-K chunks by bi-encoder similarity
            top_k_indices = sims.argsort()[::-1][:stage1_top_k]

            candidate_pool = []
            for c_idx in top_k_indices:
                candidate_pool.append({
                    "chunk": chunks[c_idx],
                    "text": chunks[c_idx].text,
                    "bi_sim": float(sims[c_idx]),
                })

            # Stage 2: Cross-Encoder precision rerank on top-K
            reranked_pool = self.reranker.rerank(
                query=req.text,
                items=candidate_pool,
                text_key="text",
                top_k=stage1_top_k,
            )

            best_entry = reranked_pool[0] if reranked_pool else None
            best_chunk: ResumeChunk | None = best_entry["chunk"] if best_entry else None
            bi_score = best_entry["bi_sim"] if best_entry else 0.0
            re_score = best_entry.get("rerank_score", bi_score) if best_entry else 0.0

            results.append({
                "requirement_text": req.text,
                "requirement_type": req.type,
                "best_chunk": best_chunk,
                "semantic_similarity": round(bi_score, 4),
                "rerank_score": round(re_score, 4),
                "top_candidates": reranked_pool,
            })

        return results


# Global singleton retriever instance
two_stage_retriever = TwoStageRetriever()

"""Phase 5 tests — Resume semantic chunking, bi-encoder retrieval, and cross-encoder reranking."""

import numpy as np
import pytest

from app.core.embeddings import (
    BiEncoder,
    CrossEncoderReranker,
    ResumeChunk,
    TwoStageRetriever,
    chunk_resume,
    find_text_offsets,
)
from app.schemas.job import Requirement


@pytest.fixture
def sample_candidate_parsed():
    return {
        "name": "Jordan Lee",
        "summary": "Experienced cloud engineer specializing in distributed systems.",
        "skills": ["Python", "Kafka", "Docker", "AWS", "PyTorch"],
        "work_experience": [
            {
                "company": "StreamingTech Corp",
                "title": "Senior Pipeline Engineer",
                "start_date": "2021-01",
                "end_date": "Present",
                "bullets": [
                    "Engineered real-time Kafka event streaming pipelines handling 50k msgs/sec.",
                    "Reduced pipeline latency by 35% through partitioning and parallel consumer groups."
                ]
            },
            {
                "company": "Legacy Systems",
                "title": "Junior Developer",
                "start_date": "2019-01",
                "end_date": "2020-12",
                "bullets": [
                    "Maintained internal company web portals using Python and HTML."
                ]
            }
        ],
        "projects": [
            {
                "name": "AudioStream",
                "description": "Personal project processing audio streams using PyTorch.",
                "technologies": ["Python", "PyTorch"]
            }
        ],
        "education": [
            {
                "institution": "Georgia Tech",
                "degree": "B.S. Computer Science",
                "year": "2018"
            }
        ]
    }


class TestResumeChunker:
    """Verify semantic chunking and provenance offset tracking."""

    def test_chunk_resume_structure(self, sample_candidate_parsed):
        raw_text = (
            "Jordan Lee\n"
            "Engineered real-time Kafka event streaming pipelines handling 50k msgs/sec.\n"
            "Maintained internal company web portals using Python and HTML.\n"
        )
        chunks = chunk_resume(sample_candidate_parsed, raw_text=raw_text)
        assert len(chunks) >= 4

        types = [c.chunk_type for c in chunks]
        assert "summary" in types
        assert "experience" in types
        assert "project" in types
        assert "skill" in types
        assert "education" in types

        # Check offsets exist for experience chunk that matched raw_text
        exp_chunks = [c for c in chunks if c.chunk_type == "experience" and "Kafka" in c.text]
        assert len(exp_chunks) == 1
        assert exp_chunks[0].start_char is not None


class TestBiEncoder:
    """Verify vector encoding, normalization, and similarity computations."""

    def test_encode_and_cosine_similarity(self):
        encoder = BiEncoder()
        texts = [
            "High-throughput streaming with Apache Kafka",
            "Real-time event data pipeline architecture",
            "Cooking Italian pasta and baking bread",
        ]
        embeddings = encoder.encode(texts)
        assert embeddings.shape == (3, embeddings.shape[1])

        # Verify normalized (L2 norm is approximately 1.0)
        norms = np.linalg.norm(embeddings, axis=1)
        for n in norms:
            assert abs(n - 1.0) < 0.05

        # Semantic check: Kafka text should be much closer to event pipelines than pasta
        sims = encoder.compute_similarity(embeddings[:1], embeddings[1:])
        sim_pipeline = sims[0][0]
        sim_pasta = sims[0][1]
        assert sim_pipeline > sim_pasta


class TestCrossEncoderReranker:
    """Verify cross-encoder precision reranking."""

    def test_rerank_snippets(self):
        reranker = CrossEncoderReranker()
        query = "Production experience with Apache Kafka message brokers"
        candidates = [
            {"id": "1", "text": "Hobby: played video games with friends."},
            {"id": "2", "text": "Architected distributed Kafka clusters streaming millions of messages."},
            {"id": "3", "text": "Designed user interface using Figma."},
        ]
        reranked = reranker.rerank(query, candidates, text_key="text", top_k=3)
        assert len(reranked) == 3
        # Top result must be the Kafka cluster snippet
        assert reranked[0]["id"] == "2"
        assert reranked[0]["rerank_score"] > reranked[2]["rerank_score"]


class TestTwoStageRetriever:
    """Verify two-stage retrieval matches requirements to specific chunks."""

    def test_retrieve_best_chunk_per_requirement(self, sample_candidate_parsed):
        chunks = chunk_resume(sample_candidate_parsed)
        retriever = TwoStageRetriever()

        requirements = [
            Requirement(
                text="Experience building distributed streaming systems with Apache Kafka",
                type="must_have",
            ),
            Requirement(
                text="Deep learning modeling with PyTorch",
                type="nice_to_have",
            ),
        ]

        matches = retriever.match_requirements_to_chunks(chunks, requirements)
        assert len(matches) == 2

        # Check Kafka requirement match
        kafka_match = matches[0]
        assert kafka_match["best_chunk"] is not None
        assert "Kafka" in kafka_match["best_chunk"].text
        assert kafka_match["best_chunk"].chunk_type == "experience"

        # Check PyTorch requirement match
        pytorch_match = matches[1]
        assert pytorch_match["best_chunk"] is not None
        assert "PyTorch" in pytorch_match["best_chunk"].text

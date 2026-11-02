"""Chat service — retrieval-grounded recruiter assistant citing candidate evidence."""

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.core.embeddings import bi_encoder, chunk_resume
from app.core.llm import get_llm_client, render_prompt
from app.models.audit_log import AuditLog
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.schemas.chat import ChatResponse, CitedSnippet
from app.schemas.llm import LLMChatResponse

logger = logging.getLogger("rankwise.chat_service")


class ChatService:
    """Recruiter assistant answering candidate pool queries grounded in evidence snippets."""

    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobRepository(db)
        self.candidate_repo = CandidateRepository(db)

    def answer_query(self, job_id: str, question: str) -> ChatResponse:
        """Answer recruiter question using retrieved snippets from candidates."""
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        candidates = self.candidate_repo.get_by_job(job_id)
        if not candidates:
            return ChatResponse(
                answer="No candidates have applied to or been uploaded for this position yet.",
                cited_snippets=[],
                confidence="none",
            )

        # 1. Collect candidate semantic chunks
        all_chunks: list[dict[str, Any]] = []
        for cand in candidates:
            cand_name = (cand.parsed_data or {}).get("name") or cand.filename
            chunks = chunk_resume(cand.parsed_data or {}, cand.raw_text or "")
            for chk in chunks:
                all_chunks.append({
                    "candidate_id": cand.id,
                    "candidate_name": cand_name,
                    "chunk": chk,
                    "text": chk.text,
                })

        if not all_chunks:
            return ChatResponse(
                answer="Candidate resumes contain no readable structured content.",
                cited_snippets=[],
                confidence="none",
            )

        # 2. Semantic retrieval on recruiter question
        q_emb = bi_encoder.encode([question])
        chunk_texts = [c["text"] for c in all_chunks]
        chunk_embs = bi_encoder.encode(chunk_texts)
        sims = bi_encoder.compute_similarity(q_emb, chunk_embs)[0]

        # Top-K relevant snippets (top 6)
        top_indices = sims.argsort()[::-1][:6]
        top_snippets = [all_chunks[idx] for idx in top_indices if sims[idx] > 0.05]

        # Format context for prompt
        if not top_snippets:
            return ChatResponse(
                answer=f"Based on the candidate records retrieved, there is no evidence of '{question}' in any candidate resume.",
                cited_snippets=[],
                confidence="low",
            )

        formatted_snippets = []
        for i, item in enumerate(top_snippets, start=1):
            formatted_snippets.append(
                f"[{i}] Candidate: {item['candidate_name']} (ID: {item['candidate_id']})\n"
                f"Evidence: \"{item['text']}\""
            )
        snippets_context = "\n---\n".join(formatted_snippets)

        # 3. LLM Generation
        llm = get_llm_client(db=self.db)
        prompt = render_prompt(
            "v1_chat_assistant.txt",
            job_title=job.title,
            candidate_snippets=snippets_context,
            question=question,
        )

        try:
            llm_resp: LLMChatResponse = llm.generate_structured(
                prompt, LLMChatResponse, temperature=0.2
            )
            # Log chat action
            audit = AuditLog(
                action="recruiter_chat",
                job_id=job_id,
                detail={"question": question, "confidence": llm_resp.confidence},
            )
            self.db.add(audit)
            self.db.commit()

            cited = [
                CitedSnippet(
                    candidate_id=s.get("candidate_id"),
                    candidate_name=s.get("candidate_name"),
                    snippet=s.get("snippet", ""),
                    relevance=s.get("relevance"),
                )
                for s in llm_resp.cited_snippets
            ]
            return ChatResponse(
                answer=llm_resp.answer,
                cited_snippets=cited,
                confidence=llm_resp.confidence,
            )

        except Exception as e:
            logger.warning(f"Chat LLM generation failed ({e}); producing grounded fallback.")
            top_cand = top_snippets[0]
            fallback_answer = (
                f"Candidate {top_cand['candidate_name']} has documented experience: \"{top_cand['text']}\""
            )
            return ChatResponse(
                answer=fallback_answer,
                cited_snippets=[
                    CitedSnippet(
                        candidate_id=top_cand["candidate_id"],
                        candidate_name=top_cand["candidate_name"],
                        snippet=top_cand["text"],
                        relevance="Most semantically similar resume section",
                    )
                ],
                confidence="medium",
            )

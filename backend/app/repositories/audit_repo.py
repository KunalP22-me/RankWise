"""Audit log repository — append-only log of all system actions."""


from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    """Data access layer for audit log entries."""

    def __init__(self, db: Session):
        self.db = db

    def log(self, action: str, **kwargs) -> AuditLog:
        """Append an audit log entry."""
        entry = AuditLog(action=action, **kwargs)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_by_job(
        self, job_id: str, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        """Get audit logs for a specific job."""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.job_id == job_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        """Get all audit logs."""
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_llm_calls(
        self, job_id: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        """Get LLM call audit logs, optionally filtered by job."""
        q = self.db.query(AuditLog).filter(AuditLog.action == "llm_call")
        if job_id:
            q = q.filter(AuditLog.job_id == job_id)
        return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

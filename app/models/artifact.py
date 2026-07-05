from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class ArtifactStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    SKIPPED = "skipped"
    FAILED = "failed"


class RepositoryArtifact(Base):
    __tablename__ = "repository_artifacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    artifact_type = Column(String, nullable=False)
    source_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(
        SQLEnum(ArtifactStatus, name="artifact_status", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=ArtifactStatus.PENDING,
    )
    normalized_data = Column(JSONB, nullable=True)
    enriched_data = Column(JSONB, nullable=True)
    merged_data = Column(JSONB, nullable=True)
    skip_reason = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    repository = relationship("Repository", back_populates="artifacts")

    __table_args__ = (
        UniqueConstraint("repository_id", "artifact_type", "source_id", name="uix_repo_artifact_source"),
    )

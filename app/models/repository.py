from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    github_repo_id = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_owner = Column(Boolean, nullable=False, default=False)
    url = Column(String, nullable=False)
    clone_path = Column(String, nullable=True)
    status = Column(
        SQLEnum(Status, name="repository_status", values_callable=lambda enum_cls: [e.value for e in enum_cls]), 
            nullable=False, 
            default=Status.ACTIVE)
    visibility = Column(
        SQLEnum(Visibility, name="repository_visibility", values_callable=lambda enum_cls: [e.value for e in enum_cls]), 
        nullable=False, 
        default=Visibility.PRIVATE
    )
    last_synced_at = Column(DateTime, nullable=True)
    default_branch = Column(String, nullable=True)
    current_branch = Column(String, nullable=True)
    understanding_percentage = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="repositories")
    conversations = relationship("Conversation", back_populates="repository", lazy="selectin")
    artifacts = relationship("RepositoryArtifact", back_populates="repository", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "github_repo_id", name="uix_user_id_github_repo_id"),
    )

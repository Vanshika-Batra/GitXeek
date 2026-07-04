from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    github_id = Column(String, nullable=True)
    github_token = Column(String, nullable=True)

    repositories = relationship("Repository", back_populates="user", lazy="selectin")
    conversations = relationship("Conversation", back_populates="user", lazy="selectin")
    messages = relationship("Message", back_populates="user", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("email", name="uix_email"),
        UniqueConstraint("github_id", name="uix_github_id"),
    )

    @property
    def github_connected(self) -> bool:
        return self.github_token is not None

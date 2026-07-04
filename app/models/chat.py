from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    messages = relationship("Message", back_populates="conversation", lazy="selectin")
    repository = relationship("Repository", back_populates="conversations")
    user = relationship("User", back_populates="conversations")

    __table_args__ = (
        UniqueConstraint("repository_id", "user_id", name="uix_repository_id_user_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    role = Column(SQLEnum(Role, name="message_role"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User", back_populates="messages")

    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uix_conversation_id_user_id"),
    )

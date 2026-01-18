"""Conversation model for chat history"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Conversation(Base):
    """
    Conversation table preserves chat history.
    - source_id: Links to documents.id or sources.id depending on source_type.
    - question/answer: Stores the full chat dialogue for RAG context and UI history.
    """
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_id = Column(Integer, nullable=False)  # ID of document or source
    source_type = Column(String, nullable=False)  # 'document', 'youtube', 'webpage'
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

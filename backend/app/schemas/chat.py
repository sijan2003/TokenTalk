"""Pydantic schemas for chat and conversations"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChatRequest(BaseModel):
    """Schema for chat request"""
    question: str
    source_id: int
    source_type: str  # 'document', 'youtube', 'webpage'


class ChatResponse(BaseModel):
    """Schema for chat response"""
    question: str
    answer: str
    timestamp: datetime


class ConversationHistory(BaseModel):
    """Schema for conversation history"""
    id: int
    source_id: int
    source_type: str
    question: str
    answer: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

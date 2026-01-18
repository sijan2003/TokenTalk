"""Pydantic schemas for documents and sources"""
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    file_type: str
    vector_store_path: Optional[str]
    status: str
    upload_date: datetime
    
    class Config:
        from_attributes = True


class SourceCreate(BaseModel):
    """Schema for creating a new source (YouTube/webpage)"""
    url: str
    source_type: str  # 'youtube' or 'webpage'


class SourceResponse(BaseModel):
    """Schema for source response"""
    id: int
    source_type: str
    url: str
    title: Optional[str]
    processed_date: datetime
    
    class Config:
        from_attributes = True


class ProcessStatus(BaseModel):
    """Schema for processing status"""
    status: str
    message: str
    id: Optional[int] = None

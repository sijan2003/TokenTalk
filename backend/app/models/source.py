"""Source model for YouTube videos and webpages"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Source(Base):
    """
    Source table tracks external content (YouTube/Webpages).
    - source_type: Identifies the extraction logic needed ('youtube' or 'webpage').
    - url: The source web link.
    - vector_store_path: Folder containing the searchable AI index for this link.
    """
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_type = Column(String, nullable=False)  # 'youtube' or 'webpage'
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    vector_store_path = Column(String, nullable=True)
    processed_date = Column(DateTime(timezone=True), server_default=func.now())

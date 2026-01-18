"""Document model for uploaded PDFs"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """
    Document table tracks uploaded PDF files.
    - user_id: Foreign key linking to the owner.
    - file_path: Path to the raw PDF in 'uploads'.
    - vector_store_path: Path to the FAISS index folder in 'vector_stores'.
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, default="pdf")
    vector_store_path = Column(String, nullable=True)
    status = Column(String, default="processing")  # 'processing', 'completed', 'failed'
    upload_date = Column(DateTime(timezone=True), server_default=func.now())

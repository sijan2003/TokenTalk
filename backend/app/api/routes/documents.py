"""API Routes for Document Management and Chat"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db, SessionLocal
from app.api.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.schemas.document import DocumentResponse
from app.schemas.chat import ChatRequest, ChatResponse, ConversationHistory
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a PDF document"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
        
    # 1. Initialize document (saves file and creates DB record)
    doc = await DocumentService.process_document(db, current_user, file)
    
    # 2. Add processing to background tasks
    background_tasks.add_task(
        DocumentService.background_process_document,
        doc.id,
        SessionLocal
    )
    
    return doc

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents for current user"""
    return DocumentService.get_user_documents(db, current_user.id)

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    DocumentService.delete_document(db, doc_id, current_user.id)

@router.post("/{doc_id}/chat", response_model=ChatResponse)
async def chat_with_document(
    doc_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with a specific document with memory"""
    # Verify document exists and belongs to user
    doc = DocumentService.get_document(db, doc_id, current_user.id)
    
    # 1. Fetch History
    history_records = db.query(Conversation).filter(
        Conversation.source_id == doc_id,
        Conversation.source_type == "document",
        Conversation.user_id == current_user.id
    ).order_by(Conversation.timestamp).all()
    
    # 2. Format for LangChain
    from app.utils.history_utils import format_chat_history
    formatted_history = format_chat_history(history_records)
    
    # 3. Generate response with history
    answer = await RAGService.generate_response(
        doc.vector_store_path,
        request.question,
        chat_history=formatted_history
    )
    
    # Save conversation
    conversation = Conversation(
        user_id=current_user.id,
        source_id=doc.id,
        source_type="document",
        question=request.question,
        answer=answer
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

@router.get("/{doc_id}/history", response_model=List[ConversationHistory])
async def get_document_history(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a document"""
    # Verify document ownership
    DocumentService.get_document(db, doc_id, current_user.id)
    
    return db.query(Conversation).filter(
        Conversation.source_id == doc_id,
        Conversation.source_type == "document",
        Conversation.user_id == current_user.id
    ).order_by(Conversation.timestamp).all()

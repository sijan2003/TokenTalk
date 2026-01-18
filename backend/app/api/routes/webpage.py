"""API Routes for Webpages"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.source import Source
from app.models.conversation import Conversation
from app.schemas.document import SourceCreate, SourceResponse
from app.schemas.chat import ChatRequest, ChatResponse, ConversationHistory
from app.services.webpage_service import WebpageService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/webpage", tags=["webpage"])

@router.post("/process", response_model=SourceResponse)
async def process_webpage(
    data: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a webpage URL"""
    return await WebpageService.process_webpage(db, current_user, data.url)

@router.get("/", response_model=List[SourceResponse])
async def list_webpages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all processed webpages"""
    return db.query(Source).filter(
        Source.user_id == current_user.id,
        Source.source_type == "webpage"
    ).all()

@router.post("/{source_id}/chat", response_model=ChatResponse)
async def chat_with_webpage(
    source_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with a specific webpage"""
    source = db.query(Source).filter(
        Source.id == source_id, 
        Source.user_id == current_user.id,
        Source.source_type == "webpage"
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Webpage not found")
        
    answer = await RAGService.generate_response(
        source.vector_store_path,
        request.question
    )
    
    conversation = Conversation(
        user_id=current_user.id,
        source_id=source.id,
        source_type="webpage",
        question=request.question,
        answer=answer
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

@router.get("/{source_id}/history", response_model=List[ConversationHistory])
async def get_webpage_history(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a webpage"""
    source = db.query(Source).filter(
        Source.id == source_id, 
        Source.user_id == current_user.id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Webpage not found")
    
    return db.query(Conversation).filter(
        Conversation.source_id == source_id,
        Conversation.source_type == "webpage",
        Conversation.user_id == current_user.id
    ).order_by(Conversation.timestamp).all()

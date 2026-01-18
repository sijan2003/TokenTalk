"""Service for processing YouTube videos"""
import os
import re
from typing import Optional
from fastapi import HTTPException, status
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from sqlalchemy.orm import Session
from app.config import settings
from app.models.source import Source
from app.models.user import User
from app.services.document_service import embeddings

class YouTubeService:
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Parses a YouTube URL to extract the unique 11-character Video ID.
        Supports standard (watch?v=) and shortened (youtu.be/) formats.
        """
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, url)
        return match.group(1) if match else None

    @staticmethod
    def get_transcript(video_id: str) -> str:
        """
        Fetches the text transcript for a given video.
        
        TECHNICAL DETAIL: This library version (1.2.3) requires an instance of 
        YouTubeTranscriptApi. It returns a list of FetchedTranscriptSnippet objects, 
        which we process to extract the raw text.
        """
        try:
            # 1. Instantiate the API class
            yt = YouTubeTranscriptApi()
            
            # 2. Fetch the transcript specifically in English variants
            transcript = yt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            
            # 3. Concatenate all text snippets into one large block.
            # We use getattr() because 'item' is an object, not a dictionary.
            return " ".join(getattr(item, "text", str(item)) for item in transcript)
            
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            # Handle cases where captions are disabled or not in requested languages
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcript unavailable for video: {str(e)}"
            )
        except Exception as e:
            # Log exact error to console for backend debugging
            print(f"❌ YouTube Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching transcript: {str(e)}"
            )

    @staticmethod
    async def process_video(
        db: Session,
        user: User,
        url: str
    ) -> Source:
        """
        The main handler for the 'Add YouTube' feature.
        1. Validates the ID
        2. Downloads the transcript
        3. Creates a local AI index (FAISS)
        4. Saves data to the database
        """
        video_id = YouTubeService.extract_video_id(url)
        if not video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL"
            )

        # 1. Fetch transcript text
        transcript_text = YouTubeService.get_transcript(video_id)
        
        # 2. Split text into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        chunks = text_splitter.create_documents([transcript_text])
        
        # 3. Create Vector Store (text -> embedding conversion)
        # We reuse the global embedding model from document_service
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # 4. Save Vector Store to local disk for persistence
        vector_store_name = f"youtube_{video_id}_faiss"
        vector_store_path = os.path.join(settings.VECTOR_STORE_DIR, str(user.id), vector_store_name)
        os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
        
        vectorstore.save_local(vector_store_path)
        
        # 5. Database logic: Create or Update source record
        existing = db.query(Source).filter(
            Source.user_id == user.id,
            Source.url == url,
            Source.source_type == "youtube"
        ).first()
        
        if existing:
            existing.vector_store_path = vector_store_path
            existing.title = f"YouTube Video ({video_id})"
            db.commit()
            db.refresh(existing)
            return existing
        
        new_source = Source(
            user_id=user.id,
            source_type="youtube",
            url=url,
            title=f"YouTube Video ({video_id})",
            vector_store_path=vector_store_path
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return new_source

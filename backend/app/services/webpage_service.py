"""Service for processing webpages"""
import os
import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from sqlalchemy.orm import Session
from app.config import settings
from app.models.source import Source
from app.models.user import User
from app.services.document_service import embeddings

class WebpageService:
    @staticmethod
    def extract_text(url: str) -> tuple[str, str]:
        """
        Downloads a webpage and extracts clean, relevant text.
        Uses BeautifulSoup to parse the HTML and filter out noise.
        """
        try:
            # 1. Set a standard User-Agent to avoid being blocked as a bot
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # 2. Fetch the page content
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 3. Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 4. Clean the noise (Scrape logic)
            # We explicitly remove non-content elements to avoid confusing the AI.
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose() # Deletes these tags from the DOM tree
                
            text = soup.get_text()
            title = soup.title.string if soup.title else url
            
            # 5. Text Cleanup (Whitespace management)
            # Removes double spaces and empty lines to save token costs.
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return clean_text, title
            
        except Exception as e:
            # Detailed error logging for development
            print(f"❌ Webpage Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error fetching webpage: {str(e)}"
            )

    @staticmethod
    async def process_webpage(
        db: Session,
        user: User,
        url: str
    ) -> Source:
        """
        The main handler for the 'Add Webpage' feature.
        1. Scrapes the site
        2. Splitting into chunks
        3. Creates a local vector index
        4. Saves record to DB
        """
        # 1. Scraping and Cleaning
        text, title = WebpageService.extract_text(url)
        
        # 2. Split text for RAG (Recursive splitting preserves semantic meaning)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        chunks = text_splitter.create_documents([text])
        
        if not chunks:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No suitable text found on webpage"
            )

        # 3. Vectorization (text -> math)
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # 4. Storage logic
        # Create a safe directory name from the end of the URL
        safe_name = "".join([c if c.isalnum() else "_" for c in url[-20:]])
        vector_store_name = f"web_{safe_name}_faiss"
        vector_store_path = os.path.join(settings.VECTOR_STORE_DIR, str(user.id), vector_store_name)
        os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
        
        # Save FAISS index locally
        vectorstore.save_local(vector_store_path)
        
        # 5. Database Logic
        existing = db.query(Source).filter(
            Source.user_id == user.id,
            Source.url == url,
            Source.source_type == "webpage"
        ).first()
        
        if existing:
            existing.vector_store_path = vector_store_path
            existing.title = title
            db.commit()
            db.refresh(existing)
            return existing
            
        new_source = Source(
            user_id=user.id,
            source_type="webpage",
            url=url,
            title=title,
            vector_store_path=vector_store_path
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return new_source

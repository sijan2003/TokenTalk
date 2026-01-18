"""Service for processing documents and managing vector stores"""
import os
import shutil
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.config import settings
from app.models.document import Document
from app.models.user import User

# Initialize the embedding model globally for the service
# HuggingFaceEmbeddings converts text chunks into mathematical vectors (384 dimensions)
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

class DocumentService:
    @staticmethod
    async def save_upload_file(file: UploadFile, user_id: int) -> str:
        """
        Saves an uploaded file to the local disk.
        Files are stored in a user-specific directory within the 'uploads' folder.
        A timestamp is prefixed to prevent filename collisions.
        """
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Unique naming convention: 20231027_123045_filename.pdf
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(user_upload_dir, filename)
        
        # Copy the file stream from FastAPI's UploadFile object to a physical file on disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_path

    @staticmethod
    async def process_document(
        db: Session,
        user: User,
        file: UploadFile
    ) -> Document:
        """
        Initializes the document entry in the database.
        The actual AI processing is handled in the background.
        """
        # Step 1: Physical File Storage
        file_path = await DocumentService.save_upload_file(file, user.id)
        
        # Step 2: Database Persistence (Initial state)
        new_doc = Document(
            user_id=user.id,
            filename=file.filename,
            file_path=file_path,
            file_type="pdf",
            status="processing"
        )
        
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return new_doc

    @staticmethod
    async def background_process_document(
        doc_id: int,
        db_factory: callable
    ):
        """
        Background task to perform text extraction and embedding generation.
        """
        db = db_factory()
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        try:
            # Step 2: Content Extraction
            loader = PyPDFLoader(doc.file_path)
            pages = loader.load()
            
            # Step 3: Text Chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            chunks = text_splitter.split_documents(pages)
            
            if not chunks:
                raise ValueError("No text extracted from document")
                
            # Step 4: Vector Store Creation (FAISS)
            vectorstore = FAISS.from_documents(chunks, embeddings)
            
            # Step 5: Save Vector Index to Disk
            vector_store_name = os.path.basename(doc.file_path) + "_faiss"
            vector_store_path = os.path.join(settings.VECTOR_STORE_DIR, str(doc.user_id), vector_store_name)
            os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
            
            vectorstore.save_local(vector_store_path)
            
            # Update Document status
            doc.vector_store_path = vector_store_path
            doc.status = "completed"
            db.commit()
            
        except Exception as e:
            print(f"Error processing document {doc_id}: {str(e)}")
            doc.status = "failed"
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_user_documents(db: Session, user_id: int):
        """Retrieves all document metadata for a specific user from the DB."""
        return db.query(Document).filter(Document.user_id == user_id).all()

    @staticmethod
    def get_document(db: Session, doc_id: int, user_id: int) -> Document:
        """Fetches a single document, ensuring it belongs to the requesting user."""
        doc = db.query(Document).filter(
            Document.id == doc_id,
            Document.user_id == user_id
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    @staticmethod
    def delete_document(db: Session, doc_id: int, user_id: int):
        """
        Hard-deletes a document:
        1. Deletes the raw PDF file
        2. Deletes the FAISS index folder
        3. Removes the database record
        """
        doc = DocumentService.get_document(db, doc_id, user_id)
        
        # 1. Delete physical source file
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass # Already gone or locked
                
        # 2. Delete the AI index (folder of .faiss and .pkl files)
        if os.path.exists(doc.vector_store_path):
            try:
                shutil.rmtree(doc.vector_store_path)
            except OSError:
                pass
                
        # 3. Finalize DB removal
        db.delete(doc)
        db.commit()

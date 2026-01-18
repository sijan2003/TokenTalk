"""Service for RAG (Retrieval Augmented Generation) operations"""
import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.config import settings

# Global AI Models initialization
# Converts text to searchable math (vectors)
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

class RAGService:
    @staticmethod
    def get_vectorstore(vector_store_path: str) -> FAISS:
        """
        Loads a FAISS index from the disk.
        
        NOTE: allow_dangerous_deserialization is required because FAISS uses the 'pickle' 
        format to store index metadata. It's safe here because we only load files 
        that our server itself created.
        """
        if not os.path.exists(vector_store_path):
            raise ValueError(f"Vector store not found at {vector_store_path}")
            
        return FAISS.load_local(
            vector_store_path, 
            embeddings,
            allow_dangerous_deserialization=True
        )

    @staticmethod
    async def generate_response(
        vector_store_path: str,
        question: str,
        chat_history: list = None
    ) -> str:
        """
        Implements an advanced RAG pipeline with Conversational Memory.
        """
        try:
            # 1. Load the searchable index
            vectorstore = RAGService.get_vectorstore(vector_store_path)
            
            # 2. Setup the Retriever
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": settings.TOP_K}
            )
            
            # 3. Connect to Gemini
            llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                google_api_key=settings.GEMINI_API_KEY,
                convert_system_message_to_human=True
            )
            
            # 4. Advanced Prompt Template
            # This prompt instructs the AI to be professional and use the history.
            prompt_template = """You are DocuMind Pro, a premium AI research assistant. 
Your goal is to provide accurate, concise, and helpful answers based ONLY on the provided context.

GUIDELINES:
- If the answer is not in the context, politely state that you don't have enough information.
- Use a professional and encouraging tone.
- Maintain consistency with the conversation history.
- Use bullet points for complex explanations.

CONVERSATION HISTORY:
{chat_history}

CONTEXT FROM SOURCES:
{context}

USER QUESTION: {question}

OFFICIAL RESPONSE:"""
            
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.messages import get_buffer_string
            
            PROMPT = PromptTemplate(
                template=prompt_template, 
                input_variables=["context", "question", "chat_history"]
            )
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            # 5. Build the Conversational Chain
            # We pass the history as a string to the prompt
            history_str = get_buffer_string(chat_history) if chat_history else "No previous history."
            
            chain = (
                {
                    "context": retriever | format_docs,
                    "question": RunnablePassthrough(),
                    "chat_history": lambda x: history_str
                }
                | PROMPT
                | llm
                | StrOutputParser()
            )
            
            # 6. Execute
            result = chain.invoke(question)
            return result
            
        except Exception as e:
            # Fallback error message if AI service or Index fails
            return f"Error gathering response: {str(e)}"

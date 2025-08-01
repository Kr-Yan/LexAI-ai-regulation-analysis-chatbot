from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from rag.vector_store import VectorStoreManager
from rag.document_processor import DocumentProcessor
from rag.chat_engine import ChatEngine

# Initialize FastAPI
app = FastAPI(title="RAG Chatbot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStoreManager(index_path="./data/vector_db")
doc_processor = DocumentProcessor()
chat_engine = ChatEngine(vector_store)

# Pydantic models
class ChatQuery(BaseModel):
    query: str

class DocumentText(BaseModel):
    text: str
    metadata: dict = {}

# Core API Routes (only what you actually use)
@app.get("/health")
async def health_check():
    doc_count = vector_store.get_document_count()
    return {
        "status": "healthy",
        "vector_store_loaded": vector_store.vector_store is not None,
        "documents_count": doc_count
    }

@app.post("/chat")
async def chat(query: ChatQuery):
    """Process a chat query"""
    response = chat_engine.chat(query.query)
    return response

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document"""
    # Validate file type
    allowed_extensions = ['.pdf', '.txt', '.md']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
        )
    
    temp_path = None
    try:
        # Save uploaded file to temp
        temp_path = f"./temp/{file.filename}"
        os.makedirs("./temp", exist_ok=True)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document for vector store
        documents = doc_processor.process_file(temp_path)
        vector_store.add_documents(documents)
        

        
        return {
            "status": "success",
            "message": f"Successfully processed {file.filename}",
            "chunks_processed": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

@app.post("/add_text")
async def add_text(doc: DocumentText):
    """Add raw text to the knowledge base"""
    try:
        # Process text for vector store
        documents = doc_processor.process_text(doc.text, doc.metadata)
        vector_store.add_documents(documents)

        
        return {
            "status": "success",
            "message": f"Processed {len(documents)} chunks",
            "chunks_processed": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear_memory")
async def clear_memory():
    """Clear conversation memory"""
    chat_engine.clear_memory()
    return {"status": "success", "message": "Memory cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
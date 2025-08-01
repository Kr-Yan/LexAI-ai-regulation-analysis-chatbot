from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import os
import shutil
from typing import List, Dict, Optional

class VectorStoreManager:
    def __init__(self, index_path: str = "./data/vector_db"):
        self.index_path = index_path
        
        # Use free HuggingFace embeddings instead of OpenAI
        print("Initializing free HuggingFace embeddings...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("Embeddings initialized successfully")
        
        self.vector_store: Optional[Chroma] = None
        self._ensure_directory_structure()
        self._load_or_create_index()
    
    def _ensure_directory_structure(self):
        """Ensure the directory structure exists"""
        os.makedirs(self.index_path, exist_ok=True)
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        try:
            if os.path.exists(os.path.join(self.index_path, "chroma.sqlite3")):
                print("Loading existing vector store...")
                self.vector_store = Chroma(
                    persist_directory=self.index_path,
                    embedding_function=self.embeddings
                )
                count = self.get_document_count()
                print(f"Loaded vector store with {count} documents")
            else:
                print("No existing vector store found - will create on first document")
                self.vector_store = None
                
        except Exception as e:
            print(f"Error loading vector store, creating new one: {e}")
            self.vector_store = None
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store"""
        if not documents:
            return
            
        try:
            # Validate and clean documents
            clean_docs = []
            for doc in documents:
                if not isinstance(doc, Document):
                    print(f"Warning: Non-Document object found: {type(doc)}")
                    continue
                
                # Ensure content is string
                if not isinstance(doc.page_content, str):
                    print(f"Warning: Non-string content found: {type(doc.page_content)}")
                    continue
                
                # Skip empty documents
                if not doc.page_content.strip():
                    continue
                
                # Ensure metadata is dict
                if not isinstance(doc.metadata, dict):
                    doc.metadata = {}
                
                clean_docs.append(doc)
            
            if not clean_docs:
                print("No valid documents to add")
                return
            
            print(f"Adding {len(clean_docs)} clean documents...")
            
            if self.vector_store is None:
                print("Creating new vector store...")
                self.vector_store = Chroma.from_documents(
                    clean_docs, 
                    self.embeddings,
                    persist_directory=self.index_path
                )
                print("Vector store created successfully")
            else:
                print("Adding to existing vector store...")
                self.vector_store.add_documents(clean_docs)
            
            # Persist to disk
            self.save()
            print(f"Successfully added {len(clean_docs)} documents to vector store")
            
        except Exception as e:
            print(f"Error adding documents: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        if not self.vector_store:
            print("Vector store not initialized - no documents added yet")
            return []
        
        try:
            # Chroma returns documents with similarity scores
            docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                query, 
                k=k
            )
            
            results = []
            for doc, score in docs_with_scores:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            print(f"Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def save(self):
        """Save the index to disk"""
        try:
            if self.vector_store:
                self.vector_store.persist()
                print("Vector store saved successfully")
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def get_document_count(self) -> int:
        """Get the number of documents in the vector store"""
        try:
            if self.vector_store:
                # Get collection info
                collection = self.vector_store._collection
                count = collection.count()
                return count
            return 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0
    
    def clear_all_documents(self):
        """Clear all documents and recreate the index"""
        try:
            # Remove the directory and recreate
            if os.path.exists(self.index_path):
                shutil.rmtree(self.index_path)
            
            self.vector_store = None
            self._ensure_directory_structure()
            print("All documents cleared from vector store")
        except Exception as e:
            print(f"Error clearing documents: {e}")
            raise
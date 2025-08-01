from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document
import os
from typing import List

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process_file(self, file_path: str, metadata: dict = {}) -> List[Document]:
        """Process a single file into chunks"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            # Load document based on type
            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_extension in ['.txt', '.md']:
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Load documents
            documents = loader.load()
            print(f"Loaded {len(documents)} pages from {file_path}")
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            print(f"Created {len(chunks)} chunks")
            
            # Clean and prepare chunks
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Create a new clean Document object
                clean_doc = Document(
                    page_content=chunk.page_content,
                    metadata={
                        "source": os.path.basename(file_path),
                        "chunk_index": i,
                        **metadata,
                        **chunk.metadata  # Include original metadata
                    }
                )
                processed_chunks.append(clean_doc)
            
            return processed_chunks
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            raise
    
    def process_text(self, text: str, metadata: dict = {}) -> List[Document]:
        """Process raw text into chunks"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            print(f"Created {len(chunks)} chunks from text")
            
            # Create clean Document objects
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "chunk_index": i,
                        "source": metadata.get("source", "Text Input"),
                        **metadata
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error processing text: {e}")
            raise
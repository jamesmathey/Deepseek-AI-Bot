import os
import json
import pandas as pd
import docx2txt
from pypdf import PdfReader
from fastapi import UploadFile
from datetime import datetime
from uuid import uuid4
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from models.schemas import DocumentInfo

class DocumentProcessor:
    def __init__(self, upload_dir: str, db_directory: str):
        self.upload_dir = upload_dir
        self.db_directory = db_directory
        self.embeddings = OllamaEmbeddings(model="deepseek-r1:32b")
        self.metadata_file = os.path.join(upload_dir, "metadata.json")
        self._ensure_directories()
        self.metadata = self._load_metadata()
        
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.db_directory, exist_ok=True)
        
    def _load_metadata(self) -> dict:
        """Load document metadata from file"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save document metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    async def process_document(self, file: UploadFile) -> DocumentInfo:
        """Process an uploaded document"""
        try:
            print(f"Starting to process document: {file.filename}")
            
            # Generate unique ID for the document
            doc_id = str(uuid4())
            print(f"Generated document ID: {doc_id}")
            
            # Save file
            file_path = os.path.join(self.upload_dir, f"{doc_id}_{file.filename}")
            print(f"Saving file to: {file_path}")
            
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            print(f"File saved successfully")
            
            # Extract text based on file type
            filename_lower = file.filename.lower()
            if filename_lower.endswith('.pdf'):
                text, total_pages = self._process_pdf(file_path)
            elif filename_lower.endswith('.docx'):
                text, total_pages = self._process_docx(file_path)
            elif filename_lower.endswith('.json'):
                text, total_pages = self._process_json(file_path)
            elif filename_lower.endswith('.csv'):
                text, total_pages = self._process_csv(file_path)
            else:
                raise ValueError(f"Unsupported file type. File must be one of: PDF, DOCX, JSON, CSV")
            
            print(f"Text extracted successfully. Total pages: {total_pages}")
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_text(text)
            print(f"Text split into {len(chunks)} chunks")
            
            # Create document metadata
            doc_info = DocumentInfo(
                id=doc_id,
                filename=file.filename,
                document_type=file.filename.split('.')[-1],
                upload_date=datetime.now(),
                total_pages=total_pages,
                status="processed",
                embedding_status="pending"
            )
            
            # Store metadata
            self.metadata[doc_id] = doc_info.model_dump()
            self._save_metadata()
            print(f"Metadata saved successfully")
            
            # Create embeddings and store in vector database
            try:
                metadata_list = [
                    {
                        "document_name": file.filename,
                        "document_id": doc_id,
                        "page_number": i + 1,
                        "chunk": i,
                    }
                    for i in range(len(chunks))
                ]
                
                print(f"Creating vector store...")
                vectorstore = Chroma(
                    persist_directory=self.db_directory,
                    embedding_function=self.embeddings
                )
                
                print(f"Adding texts to vector store...")
                vectorstore.add_texts(
                    texts=chunks,
                    metadatas=metadata_list
                )
                
                # Update embedding status
                doc_info.embedding_status = "completed"
                self.metadata[doc_id].update({"embedding_status": "completed"})
                self._save_metadata()
                print(f"Document processing completed successfully")
                
            except Exception as e:
                print(f"Error creating embeddings: {str(e)}")
                doc_info.embedding_status = "failed"
                self.metadata[doc_id].update({"embedding_status": "failed"})
                self._save_metadata()
                raise Exception(f"Failed to create embeddings: {str(e)}")
            
            return doc_info
            
        except Exception as e:
            print(f"Error in process_document: {str(e)}")
            raise
    
    def _process_pdf(self, file_path: str) -> tuple[str, int]:
        """Extract text from PDF file"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text, len(reader.pages)
    
    def _process_docx(self, file_path: str) -> tuple[str, int]:
        """Extract text from DOCX file"""
        text = docx2txt.process(file_path)
        # Approximate page count based on characters (average 3000 chars per page)
        total_pages = max(1, len(text) // 3000)
        return text, total_pages
    
    def _process_json(self, file_path: str) -> tuple[str, int]:
        """Extract text from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        text = json.dumps(data, indent=2)
        # Consider each top-level key as a page
        total_pages = max(1, len(data.keys()) if isinstance(data, dict) else 1)
        return text, total_pages
    
    def _process_csv(self, file_path: str) -> tuple[str, int]:
        """Extract text from CSV file"""
        df = pd.read_csv(file_path)
        text = df.to_string()
        # Consider each 100 rows as a page
        total_pages = max(1, len(df) // 100)
        return text, total_pages
    
    async def list_documents(self) -> list[DocumentInfo]:
        """List all processed documents"""
        return [DocumentInfo(**doc_data) for doc_data in self.metadata.values()] 
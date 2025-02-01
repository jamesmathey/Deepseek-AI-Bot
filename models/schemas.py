from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class Source(BaseModel):
    document_name: str
    page_number: int
    content_snippet: str

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[Source]] = None
    conversation_id: Optional[str] = None
    user_message: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class DocumentInfo(BaseModel):
    id: str
    filename: str
    document_type: str
    upload_date: datetime
    total_pages: Optional[int]
    status: str
    embedding_status: str
    error: Optional[str] = None

class ExportRequest(BaseModel):
    conversation_id: str
    format: str

    def model_dump(self):
        return {
            "conversation_id": self.conversation_id,
            "format": self.format
        }

class ExportResponse(BaseModel):
    file_name: str

    def model_dump(self):
        return {
            "file_name": self.file_name
        } 
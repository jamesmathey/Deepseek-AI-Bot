from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import os
from dotenv import load_dotenv
from services.document_processor import DocumentProcessor
from services.chat_service import ChatService
from services.export_service import ExportService
from models.schemas import ChatResponse, DocumentInfo, ChatRequest, ExportRequest, ExportResponse

load_dotenv()

app = FastAPI(title="AI Document Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
UPLOAD_DIR = os.path.join(os.getcwd(), "uploaded_documents")
DB_DIR = os.path.join(os.getcwd(), "vector_db")
EXPORT_DIR = os.path.join(os.getcwd(), "exported_chats")

document_processor = DocumentProcessor(upload_dir=UPLOAD_DIR, db_directory=DB_DIR)
chat_service = ChatService(db_directory=DB_DIR)
export_service = ExportService(export_dir=EXPORT_DIR)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, JSON, CSV) for processing
    """
    try:
        # Log file information
        print(f"Received file: {file.filename}")
        print(f"Content type: {file.content_type}")
        
        # Validate file type
        allowed_types = {'.pdf', '.docx', '.json', '.csv'}
        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        
        print(f"File extension: {file_ext}")
        
        if not file_ext:
            raise HTTPException(
                status_code=400,
                detail=f"File must have an extension. Allowed types: {', '.join(allowed_types)}"
            )
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file_ext}'. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Process the document
        doc_info = await document_processor.process_document(file)
        return {"message": "Document processed successfully", "document_info": doc_info}
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the AI about the uploaded documents
    """
    try:
        return StreamingResponse(
            chat_service.get_streaming_response(
                message=request.message,
                conversation_id=request.conversation_id
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all processed documents
    """
    try:
        documents = await document_processor.list_documents()
        return documents
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export", response_model=ExportResponse)
async def export_chat(request: ExportRequest):
    try:
        # Get conversation history
        messages = chat_service.get_conversation_history(request.conversation_id)
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Export the conversation
        filename = export_service.export_chat(messages, request.conversation_id, request.format)
        
        # Return proper response model
        return ExportResponse(file_name=filename)
    except Exception as e:
        print(f"Export error: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    try:
        file_path = export_service.get_export_path(filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        print(f"Download error: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
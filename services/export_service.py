import os
from typing import Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models.schemas import ChatResponse

class ExportService:
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

    def _create_filename(self, conversation_id: str, format: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"chat_export_{conversation_id}_{timestamp}.{format}"

    def export_to_txt(self, messages: list[ChatResponse], conversation_id: str) -> str:
        filename = self._create_filename(conversation_id, "txt")
        filepath = os.path.join(self.export_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for msg in messages:
                # Write user message
                f.write(f"User: {msg.user_message}\n\n")
                
                # Write assistant response
                f.write(f"Assistant: {msg.response}\n")
                
                # Write sources if available
                if msg.sources:
                    f.write("\nSources:\n")
                    for source in msg.sources:
                        f.write(f"- {source.document_name} (Page {source.page_number})\n")
                
                f.write("\n" + "-"*80 + "\n\n")
        
        return filename

    def export_to_pdf(self, messages: list[ChatResponse], conversation_id: str) -> str:
        filename = self._create_filename(conversation_id, "pdf")
        filepath = os.path.join(self.export_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        normal_style = styles['Normal']
        user_style = ParagraphStyle(
            'UserStyle',
            parent=styles['Normal'],
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=12
        )
        assistant_style = ParagraphStyle(
            'AssistantStyle',
            parent=styles['Normal'],
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )
        source_style = ParagraphStyle(
            'SourceStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            leftIndent=20
        )
        
        # Build document content
        content = []
        
        # Add title
        content.append(Paragraph("Chat Export", title_style))
        content.append(Spacer(1, 20))
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"Exported on: {timestamp}", normal_style))
        content.append(Spacer(1, 20))
        
        for msg in messages:
            # Add user message
            content.append(Paragraph(f"User: {msg.user_message}", user_style))
            
            # Add assistant response
            content.append(Paragraph(f"Assistant: {msg.response}", assistant_style))
            
            # Add sources if available
            if msg.sources:
                content.append(Paragraph("Sources:", source_style))
                for source in msg.sources:
                    content.append(Paragraph(
                        f"• {source.document_name} (Page {source.page_number})",
                        source_style
                    ))
            
            content.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(content)
        return filename

    def export_chat(self, messages: list[ChatResponse], conversation_id: str, format: str = "pdf") -> str:
        """Export chat conversation to the specified format"""
        try:
            # Ensure messages are properly serialized
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    formatted_messages.append(ChatResponse(**msg))
                else:
                    formatted_messages.append(msg)

            if format.lower() == "pdf":
                return self.export_to_pdf(formatted_messages, conversation_id)
            elif format.lower() == "txt":
                return self.export_to_txt(formatted_messages, conversation_id)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            print(f"Error in export_chat: {str(e)}")
            raise

    def get_export_path(self, filename: str) -> str:
        """Get the full path of an exported file"""
        return os.path.join(self.export_dir, filename) 
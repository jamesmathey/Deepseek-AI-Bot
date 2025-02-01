import os
from typing import Optional, List, AsyncGenerator
from uuid import uuid4
from fastapi import WebSocket
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from models.schemas import ChatResponse, Source
from langchain.prompts import ChatPromptTemplate
import json
import asyncio

class ChatService:
    def __init__(self, db_directory: str):
        self.db_directory = db_directory
        self.conversations_dir = os.path.join(db_directory, "conversations")
        if not os.path.exists(self.conversations_dir):
            os.makedirs(self.conversations_dir)
            
        self.embeddings = OllamaEmbeddings(model="deepseek-r1:32b")
        self.llm = ChatOllama(
            model="deepseek-r1:32b",
            temperature=0.7,
            streaming=True
        )
        self.conversations = self._load_conversations()
        
        self.system_message = SystemMessage(content="""You are a helpful AI assistant that answers questions based on the provided context. 
Always provide detailed, accurate responses and cite your sources when possible. 
When you're thinking or analyzing, start your response with '<think>' and end with '</think>' before providing your final answer.""")

    def _load_conversations(self) -> dict:
        """Load all conversations from disk"""
        conversations = {}
        if os.path.exists(self.conversations_dir):
            for filename in os.listdir(self.conversations_dir):
                if filename.endswith('.json'):
                    conv_id = filename[:-5]  # Remove .json extension
                    filepath = os.path.join(self.conversations_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            conv_data = json.load(f)
                            # Reconstruct ChatResponse objects
                            if 'messages' in conv_data:
                                conv_data['messages'] = [
                                    ChatResponse(**msg) if isinstance(msg, dict) else msg 
                                    for msg in conv_data['messages']
                                ]
                            # Initialize vectorstore
                            conv_data['vectorstore'] = Chroma(
                                persist_directory=self.db_directory,
                                embedding_function=self.embeddings
                            )
                            conversations[conv_id] = conv_data
                    except Exception as e:
                        print(f"Error loading conversation {conv_id}: {str(e)}")
        return conversations

    def _save_conversation(self, conversation_id: str):
        """Save a conversation to disk"""
        if conversation_id in self.conversations:
            filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            conv_data = self.conversations[conversation_id].copy()
            # Remove non-serializable objects
            conv_data.pop('vectorstore', None)
            # Convert ChatResponse objects to dicts
            if 'messages' in conv_data:
                conv_data['messages'] = [
                    msg.model_dump() if hasattr(msg, 'model_dump') else msg 
                    for msg in conv_data['messages']
                ]
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(conv_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving conversation {conversation_id}: {str(e)}")

    def _get_or_create_conversation(self, conversation_id: Optional[str] = None) -> dict:
        """Get or create a conversation with proper initialization"""
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        new_id = conversation_id or str(uuid4())
        vectorstore = Chroma(
            persist_directory=self.db_directory,
            embedding_function=self.embeddings
        )
        
        self.conversations[new_id] = {
            'id': new_id,
            'vectorstore': vectorstore,
            'history': [],
            'messages': []
        }
        self._save_conversation(new_id)
        return self.conversations[new_id]

    async def get_streaming_response(self, message: str, conversation_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        try:
            # Setup conversation
            conversation = self._get_or_create_conversation(conversation_id)
            vectorstore = conversation['vectorstore']
            history = conversation['history']
            conv_id = conversation['id']

            # Search for relevant documents
            docs = vectorstore.similarity_search(message, k=3)
            context = "\n".join(doc.page_content for doc in docs)
            
            # Create sources list
            sources = [
                Source(
                    document_name=doc.metadata.get("document_name", "Unknown"),
                    page_number=doc.metadata.get("page_number", 1),
                    content_snippet=doc.page_content[:200] + "..."
                )
                for doc in docs
            ]

            # Send initial thinking state
            thinking_response = "<think>Analyzing the context and formulating a response...</think>\n"
            yield json.dumps({
                "response": thinking_response,
                "sources": [s.model_dump() for s in sources],
                "conversation_id": conv_id,
                "user_message": message
            }) + "\n"

            # Small delay to show thinking state
            await asyncio.sleep(0.5)

            try:
                # Create message list with system message and context
                messages = [
                    self.system_message,
                    HumanMessage(content=f"Context: {context}\n\nQuestion: {message}")
                ]

                # Add conversation history if it exists
                if history:
                    messages.extend(history[-4:])  # Add last 2 exchanges (4 messages)

                # Start the streaming response
                full_response = ""
                async for chunk in self.llm.astream(messages):
                    if hasattr(chunk, 'content'):
                        full_response += chunk.content
                        yield json.dumps({
                            "response": full_response,
                            "sources": [s.model_dump() for s in sources],
                            "conversation_id": conv_id,
                            "user_message": message
                        }) + "\n"

                # Create the final chat response
                chat_response = ChatResponse(
                    response=full_response,
                    sources=sources,
                    conversation_id=conv_id,
                    user_message=message
                )

                # Update conversation history
                history.extend([
                    HumanMessage(content=message),
                    AIMessage(content=full_response)
                ])
                
                # Store the complete message and save
                conversation['messages'].append(chat_response)
                self._save_conversation(conv_id)

            except Exception as e:
                print(f"Streaming error: {str(e)}")
                raise

        except Exception as e:
            print(f"Error during chat: {str(e)}")
            error_response = {
                "response": "I apologize, but I encountered an error while processing your request.",
                "sources": [s.model_dump() for s in sources] if 'sources' in locals() else [],
                "conversation_id": conv_id if 'conv_id' in locals() else str(uuid4()),
                "user_message": message
            }
            yield json.dumps(error_response) + "\n"

    def get_conversation_history(self, conversation_id: str) -> list[ChatResponse]:
        """Get the complete conversation history"""
        if conversation_id not in self.conversations:
            print(f"Conversation {conversation_id} not found")
            print(f"Available conversations: {list(self.conversations.keys())}")
            return []
            
        conversation = self.conversations[conversation_id]
        if 'messages' not in conversation:
            print(f"No messages in conversation {conversation_id}")
            return []
            
        return conversation['messages'] 
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ConversationHistory(BaseModel):
    id: Optional[str] = None
    session_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

class Document(BaseModel):
    id: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[list] = None
    created_at: Optional[datetime] = None

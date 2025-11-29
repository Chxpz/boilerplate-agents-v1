from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(default="default", description="Session identifier")


class ChatResponse(BaseModel):
    response: str
    context: Optional[str] = None
    session_id: str


class DocumentRequest(BaseModel):
    texts: List[str] = Field(..., description="List of text documents to add")
    metadata: Optional[List[dict]] = None


class DocumentResponse(BaseModel):
    count: int
    message: str

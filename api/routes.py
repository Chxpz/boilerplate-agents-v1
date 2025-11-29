from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from api.schemas import ChatRequest, ChatResponse, DocumentRequest, DocumentResponse
from agent import agent_executor
from core import rag_manager, memory_manager
from config import settings
import json
import asyncio

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """Chat endpoint for agent interaction."""
    try:
        result = await agent_executor.execute(
            user_input=chat_request.message,
            session_id=chat_request.session_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """Streaming chat endpoint for agent interaction."""
    async def generate():
        try:
            async for chunk in agent_executor.execute_stream(
                user_input=chat_request.message,
                session_id=chat_request.session_id
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.005)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/documents", response_model=DocumentResponse)
@limiter.limit("10/minute")
async def add_documents(request: Request, doc_request: DocumentRequest):
    """Add documents to the RAG system."""
    try:
        count = rag_manager.add_texts(
            texts=doc_request.texts,
            metadatas=doc_request.metadatas
        )
        return DocumentResponse(
            count=count,
            message=f"Successfully added {count} document chunks"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """Clear conversation memory for a session."""
    try:
        memory_manager.clear_session(session_id)
        return {"message": f"Memory cleared for session: {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    from core import ModelManager, redis_client
    from config import settings
    
    health = {
        "status": "healthy",
        "services": {}
    }
    
    try:
        ModelManager.get_llm()
        health["services"]["llm"] = "ok"
    except Exception as e:
        health["services"]["llm"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    try:
        rag_manager.initialize_vectorstore()
        health["services"]["vectorstore"] = "ok"
    except Exception as e:
        health["services"]["vectorstore"] = f"error: {str(e)}"
        health["status"] = "degraded"
    
    if settings.redis_enabled:
        try:
            redis = redis_client.get_async_client()
            await redis.ping()
            health["services"]["redis"] = "ok"
        except Exception as e:
            health["services"]["redis"] = f"error: {str(e)}"
            health["status"] = "degraded"
    
    return health

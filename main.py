from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from api import router
from config import settings
from core.middleware import error_handler_middleware, logging_middleware
from core.logger import logger
import uvicorn

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Agent API",
    description="LangChain + LangGraph AI Agent with RAG, Memory, and MCP",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)
app.middleware("http")(error_handler_middleware)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting AI Agent API...")
    logger.info(f"Server running on {settings.api_host}:{settings.api_port}")
    
    try:
        from core import ModelManager, redis_client
        ModelManager.get_llm()
        logger.info("LLM initialized successfully")
        
        if settings.redis_enabled:
            redis = redis_client.get_async_client()
            await redis.ping()
            logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    from core import mcp_client, redis_client, event_bus
    
    await event_bus.stop_consumer()
    await mcp_client.close()
    await redis_client.close()
    
    logger.info("Shutting down AI Agent API...")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

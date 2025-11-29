from fastapi import Request, status
from fastapi.responses import JSONResponse
from core.logger import logger
import time

async def error_handler_middleware(request: Request, call_next):
    """Global error handling middleware."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )

async def logging_middleware(request: Request, call_next):
    """Request/response logging middleware."""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {duration:.2f}s")
    
    return response

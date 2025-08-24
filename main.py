
"""
QueryForge FastAPI Application
REST API for natural language to SQL/NoSQL query generation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from core.config import Config
from core.models import QueryRequest, QueryResponse, HealthResponse, ModelsResponse, Schema
from core.generator import generator
from core.storage import SchemaStorage

# Initialize FastAPI app
app = FastAPI(
    title="QueryForge API",
    description="Natural language to SQL/NoSQL query generation",
    version="1.0.0",
    docs_url="/docs" if Config.is_api_key_configured() else None,
    redoc_url="/redoc" if Config.is_api_key_configured() else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for production error handling."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with logging."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)

# Initialize storage
storage = SchemaStorage()

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        ok=True,
        provider=Config.PROVIDER,
        apiKeyConfigured=Config.is_api_key_configured()
    )

@app.get("/api/models", response_model=ModelsResponse)
async def get_models():
    """Get available AI models."""
    try:
        return ModelsResponse(models=Config.OPENAI_MODELS)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/api/generate-query", response_model=QueryResponse)
async def generate_query(request: QueryRequest):
    """Generate SQL query from natural language."""
    try:
        query, error = await generator.generate_query(
            question=request.question,
            database_type=request.databaseType,
            model=request.model or Config.MODEL_CHAT,
            schema_text=request.schemaText,
            schema_id=request.schemaId,
            strict=request.strict or True,
            row_limit=request.row_limit or Config.ROW_LIMIT_DEFAULT
        )
        
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return QueryResponse(sql=query)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

@app.get("/api/schemas", response_model=list[Schema])
async def get_schemas():
    """Get all schemas."""
    try:
        return storage.list_schemas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schemas", response_model=Schema)
async def create_schema(schema: Schema):
    """Create a new schema."""
    try:
        return storage.save_schema(schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/schemas/{schema_id}")
async def delete_schema(schema_id: str):
    """Delete a schema."""
    try:
        storage.delete_schema(schema_id)
        return {"message": "Schema deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

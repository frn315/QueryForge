"""
Data models for QueryForge.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Schema(BaseModel):
    """Database schema model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    database_type: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_dump(self, **kwargs):
        """Custom serialization to handle datetime."""
        data = super().model_dump(**kwargs)
        # Convert datetime objects to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

class QueryRequest(BaseModel):
    """Request model for query generation."""
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    databaseType: str = Field(..., description="Target database type")
    model: Optional[str] = Field(None, description="AI model to use")
    schemaText: Optional[str] = Field(None, description="Database schema as text")
    schemaId: Optional[str] = Field(None, description="ID of saved schema to use")
    strict: Optional[bool] = Field(True, description="Whether to enforce safety checks")
    row_limit: Optional[int] = Field(None, description="Maximum rows to return")

class QueryResponse(BaseModel):
    """Response model for query generation."""
    sql: str = Field(..., description="Generated SQL query")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")

class HealthResponse(BaseModel):
    """Health check response."""
    ok: bool = Field(..., description="Service health status")
    provider: str = Field(..., description="AI provider name")
    apiKeyConfigured: bool = Field(..., description="API key configuration status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ModelsResponse(BaseModel):
    """Available models response."""
    models: list[str] = Field(..., description="List of available AI models")
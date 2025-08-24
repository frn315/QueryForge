"""
Schema storage management for QueryForge.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import Config
from .models import Schema

class SchemaStorage:
    """File-based schema storage manager."""

    def __init__(self):
        self.storage_dir = Path(Config.STORAGE_DIR)
        self.schemas_dir = self.storage_dir / "schemas"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure storage directories exist."""
        self.schemas_dir.mkdir(parents=True, exist_ok=True)

    def save_schema(self, schema: Schema) -> Schema:
        """Save a schema to storage."""
        if not schema.id:
            schema.id = self._generate_id()

        schema.updated_at = datetime.now()

        file_path = self.schemas_dir / f"{schema.id}.json"

        with open(file_path, 'w') as f:
            json.dump(schema.model_dump(), f, indent=2, default=str)

        return schema

    def load_schema(self, schema_id: str) -> Optional[Schema]:
        """Load a schema from storage."""
        file_path = self.schemas_dir / f"{schema_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return Schema(**data)
        except Exception:
            return None

    def list_schemas(self) -> List[Schema]:
        """List all schemas in storage."""
        schemas = []

        for file_path in self.schemas_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                schemas.append(Schema(**data))
            except Exception:
                continue

        # Sort by updated_at descending
        schemas.sort(key=lambda s: s.updated_at, reverse=True)
        return schemas

    def delete_schema(self, schema_id: str) -> bool:
        """Delete a schema from storage."""
        file_path = self.schemas_dir / f"{schema_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def _generate_id(self) -> str:
        """Generate a unique ID for a schema."""
        import uuid
        return str(uuid.uuid4())
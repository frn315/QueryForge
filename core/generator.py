
"""
High-level query generation functionality.
"""

import asyncio
import logging
from typing import Optional, Tuple
from .config import Config
from .models import Schema
from .storage import SchemaStorage
from .prompting import build_system_prompt, build_user_prompt, validate_prompt_inputs
from .provider_openai import OpenAIProvider
from .safety import validate_query_safety, clean_query_response, sanitize_input

logger = logging.getLogger(__name__)

class QueryGenerator:
    """Main query generation service."""

    def __init__(self):
        self.provider = OpenAIProvider()
        self.storage = SchemaStorage()

    async def generate_query(
        self,
        question: str,
        database_type: str,
        model: Optional[str] = None,
        schema_text: Optional[str] = None,
        schema_id: Optional[str] = None,
        strict: bool = True,
        row_limit: Optional[int] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Generate SQL query from natural language.

        Args:
            question: Natural language question
            database_type: Target database type
            model: AI model to use (defaults to config default)
            schema_text: Schema definition text
            schema_id: ID of saved schema to use
            strict: Whether to enforce safety checks
            row_limit: Maximum rows to return

        Returns:
            Tuple of (generated_query, error_message)
        """

        try:
            # Sanitize inputs
            question = sanitize_input(question)

            # Validate inputs
            is_valid, error_msg = validate_prompt_inputs(question, database_type)
            if not is_valid:
                return "", error_msg

            if database_type not in Config.SUPPORTED_DATABASES:
                return "", f"Unsupported database type: {database_type}. Supported: {', '.join(Config.SUPPORTED_DATABASES)}"

            # Check API configuration
            if not self.provider.is_configured():
                return "", "OpenAI API key not configured or invalid"

            # Validate row limit
            if row_limit is not None:
                if row_limit < 1:
                    return "", "Row limit must be at least 1"
                if row_limit > Config.ROW_LIMIT_MAX:
                    return "", f"Row limit cannot exceed {Config.ROW_LIMIT_MAX}"

            # Use default model if not specified
            if not model:
                model = Config.MODEL_CHAT

            # Resolve schema content
            schema_content = schema_text
            if schema_id and not schema_content:
                stored_schema = self.storage.load_schema(schema_id)
                if stored_schema:
                    schema_content = stored_schema.content
                else:
                    return "", f"Schema with ID {schema_id} not found"

            # Build prompts
            system_prompt = build_system_prompt()
            user_prompt = build_user_prompt(
                question=question,
                database_type=database_type,
                schema_content=schema_content,
                strict=strict,
                row_limit=row_limit
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM
            response = await self.provider.chat_completion(
                model=model,
                messages=messages,
                temperature=0.1
            )

            # Clean up response
            query = clean_query_response(response)

            # Validate safety
            if strict:
                is_safe, violations = validate_query_safety(query, database_type, strict)
                if not is_safe:
                    violation_text = "; ".join(violations)
                    return "", f"Query contains unsafe operations: {violation_text}"

            return query, None

        except Exception as e:
            logger.error(f"Query generation error: {str(e)}", exc_info=True)
            return "", f"Generation error: {str(e)}"

    def get_available_models(self) -> list:
        """Get list of available models."""
        return self.provider.get_available_models()

    def is_configured(self) -> bool:
        """Check if the generator is properly configured."""
        return self.provider.is_configured()

# Create singleton instance
generator = QueryGenerator()

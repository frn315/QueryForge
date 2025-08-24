
"""
Prompt engineering for QueryForge.
"""

from typing import Optional

def build_system_prompt() -> str:
    """Build the system prompt for the AI model."""
    return """You are QueryForge, a professional SQL/NoSQL query generator.

CRITICAL RULES:
1. Generate ONLY the requested query - no explanations, markdown, or extra text
2. Return valid, executable SQL/MongoDB aggregation pipelines
3. Use proper syntax for the specified database type
4. Include appropriate JOINs for related tables when needed
5. Always add LIMIT clauses to prevent excessive data retrieval
6. Use parameterized query patterns when possible
7. Optimize for performance and readability

SAFETY REQUIREMENTS:
- In strict mode, generate ONLY SELECT statements
- Never generate DDL (CREATE, DROP, ALTER) or DML (INSERT, UPDATE, DELETE) unless explicitly requested
- Avoid system functions and administrative operations
- Use proper escaping for string literals

QUALITY STANDARDS:
- Use consistent formatting and indentation
- Include meaningful column aliases
- Use appropriate aggregate functions
- Handle NULL values appropriately
- Follow database-specific best practices"""

def build_user_prompt(
    question: str,
    database_type: str,
    schema_content: Optional[str] = None,
    strict: bool = True,
    row_limit: Optional[int] = None
) -> str:
    """Build the user prompt with context."""
    
    # Set default row limit if not provided
    if row_limit is None:
        row_limit = 1000
    
    # Build the base prompt
    prompt_parts = [
        f"Database Type: {database_type}",
        f"Question: {question}"
    ]
    
    # Add schema information if provided
    if schema_content:
        prompt_parts.extend([
            "",
            "Database Schema:",
            schema_content.strip()
        ])
    
    # Add mode information
    mode = "strict mode (SELECT-only)" if strict else "flexible mode"
    prompt_parts.extend([
        "",
        f"Mode: {mode}",
        f"Row Limit: {row_limit}"
    ])
    
    # Add database-specific instructions
    if database_type.lower() == "mongodb":
        prompt_parts.extend([
            "",
            "Generate a MongoDB aggregation pipeline as a JSON array.",
            "Use proper MongoDB operators and syntax.",
            "Include $limit stage at the end."
        ])
    elif database_type.lower() in ["mysql", "postgresql", "sql server", "sqlite", "oracle"]:
        prompt_parts.extend([
            "",
            f"Generate a {database_type} query.",
            "Use appropriate SQL dialect features.",
            "Include LIMIT/TOP clause for row limiting.",
            "Use proper JOIN syntax when accessing multiple tables."
        ])
    
    prompt_parts.extend([
        "",
        "Return ONLY the query without any explanation or formatting."
    ])
    
    return "\n".join(prompt_parts)

def validate_prompt_inputs(question: str, database_type: str) -> tuple[bool, str]:
    """Validate prompt inputs for safety and completeness."""
    
    if not question or not question.strip():
        return False, "Question cannot be empty"
    
    if len(question) > 1000:
        return False, "Question is too long (max 1000 characters)"
    
    if not database_type or not database_type.strip():
        return False, "Database type must be specified"
    
    # Check for potential injection in question
    dangerous_patterns = [
        r';\s*(DROP|DELETE|INSERT|UPDATE)',
        r'EXEC\s*\(',
        r'xp_cmdshell',
        r'sp_executesql',
    ]
    
    import re
    for pattern in dangerous_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            return False, "Question contains potentially unsafe content"
    
    return True, ""

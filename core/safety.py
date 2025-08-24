"""
Safety checks for generated queries.
"""

import re
import json
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

UNSAFE_SQL_KEYWORDS = [
    "CREATE", "ALTER", "DROP", "TRUNCATE",
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT",
    "GRANT", "REVOKE",
    "COMMIT", "ROLLBACK", "SAVEPOINT",
    "EXEC", "EXECUTE", "CALL", "PROCEDURE", "FUNCTION",
    "INDEX", "TRIGGER", "VIEW", "SCHEMA", "DATABASE",
    "USER", "ROLE", "LOGIN", "PASSWORD",
    "SLEEP", "WAITFOR", "BENCHMARK", "LOAD_FILE", "INTO OUTFILE"
]

UNSAFE_MONGO_OPERATIONS = [
    "$out", "$merge", "$addFields", "$set", "$unset",
    "$replaceRoot", "$replaceWith", "insertOne", "insertMany",
    "updateOne", "updateMany", "deleteOne", "deleteMany",
    "replaceOne", "findOneAndUpdate", "findOneAndDelete",
    "findOneAndReplace", "bulkWrite", "createIndex", "dropIndex"
]

def sanitize_input(text: str) -> str:
    """Sanitize user input by removing dangerous patterns."""
    if not text:
        return ""

    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Limit length
    if len(text) > 2000:
        text = text[:2000]

    # Remove excessive whitespace
    text = ' '.join(text.split())

    return text.strip()

def clean_query_response(response: str) -> str:
    """Clean and format the AI model response."""
    if not response:
        return ""

    # Remove markdown code blocks
    response = re.sub(r'```(?:sql|json|mongodb)?\n?', '', response, flags=re.IGNORECASE)
    response = re.sub(r'```', '', response)

    # Remove extra whitespace and newlines
    response = response.strip()

    # Remove common AI response prefixes
    prefixes_to_remove = [
        "Here's the SQL query:",
        "Here's the query:",
        "The query is:",
        "Query:",
        "SQL:",
        "MongoDB:",
    ]

    for prefix in prefixes_to_remove:
        if response.lower().startswith(prefix.lower()):
            response = response[len(prefix):].strip()

    return response

def validate_query_safety(query: str, database_type: str, strict: bool = True) -> Tuple[bool, List[str]]:
    """
    Validate query for safety violations.

    Returns:
        Tuple of (is_safe, list_of_violations)
    """
    if not query or not query.strip():
        return False, ["Empty query"]

    violations = []

    # Database-specific validation
    if database_type.lower() == "mongodb":
        violations.extend(_validate_mongodb_query(query, strict))
    else:
        violations.extend(_validate_sql_query(query, strict))

    # Generic safety checks
    violations.extend(_validate_generic_safety(query))

    return len(violations) == 0, violations

def _validate_sql_query(query: str, strict: bool) -> List[str]:
    """Validate SQL query for safety."""
    violations = []
    query_upper = query.upper()

    if strict:
        trimmed_query = query.strip().upper()
        if not trimmed_query.startswith("SELECT") and not trimmed_query.startswith("WITH"):
            violations.append("Only SELECT statements allowed in strict mode")

    for keyword in UNSAFE_SQL_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_upper):
            violations.append(f"Unsafe SQL keyword detected: {keyword}")

    injection_patterns = [
        r';\s*(DROP|DELETE|INSERT|UPDATE)',
        r'UNION\s+ALL\s+SELECT',
        r'--\s*\w+',
        r'/\*.*?\*/',
    ]

    for pattern in injection_patterns:
        if re.search(pattern, query, re.IGNORECASE | re.DOTALL):
            violations.append("Potential SQL injection pattern detected")

    return violations

def _validate_mongodb_query(query: str, strict: bool) -> List[str]:
    """Validate MongoDB query for safety."""
    violations = []

    try:
        if query.strip().startswith('[') or query.strip().startswith('{'):
            parsed = json.loads(query)
        else:
            query_upper = query.upper()
            if any(op in query_upper for op in ["INSERTONE", "INSERTMANY", "UPDATEONE", "UPDATEMANY", "DELETEONE", "DELETEMANY"]):
                violations.append("MongoDB write operations not allowed in strict mode")

        for operation in UNSAFE_MONGO_OPERATIONS:
            if operation in query:
                violations.append(f"Unsafe MongoDB operation detected: {operation}")

    except json.JSONDecodeError:
        violations.append("Invalid MongoDB query format")

    return violations

def _validate_generic_safety(query: str) -> List[str]:
    """Generic safety validation for all query types."""
    violations = []

    # Check for system commands
    system_patterns = [
        r'xp_cmdshell',
        r'sp_executesql',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'os\.',
        r'import\s+os',
        r'subprocess',
    ]

    for pattern in system_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            violations.append("System command detected")

    # Check for file operations
    file_patterns = [
        r'LOAD_FILE',
        r'INTO\s+OUTFILE',
        r'LOAD\s+DATA',
        r'SELECT\s+.*\s+INTO\s+DUMPFILE',
    ]

    for pattern in file_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            violations.append("File operation detected")

    return violations
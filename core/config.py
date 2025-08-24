
"""
Configuration management for QueryForge.
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

def write_env(key: str, value: str) -> bool:
    """Write environment variable to .env file."""
    try:
        env_path = Path(".env")
        if not env_path.exists():
            env_path.touch()
        
        set_key(str(env_path), key, value)
        os.environ[key] = value
        return True
    except Exception:
        return False

class Config:
    """Application configuration."""
    
    # Provider settings
    PROVIDER = "OpenAI"
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Model settings
    MODEL_CHAT = "gpt-3.5-turbo"
    
    OPENAI_MODELS = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4",
        "gpt-4-turbo-preview",
        "gpt-4o",
        "gpt-4o-mini"
    ]
    
    # Database settings
    SUPPORTED_DATABASES = [
        "MySQL",
        "PostgreSQL", 
        "SQL Server",
        "SQLite",
        "Oracle",
        "MongoDB"
    ]
    
    # Storage settings
    STORAGE_DIR = Path("storage")
    
    # Query limits
    ROW_LIMIT_DEFAULT = int(os.getenv("ROW_LIMIT_DEFAULT", "1000"))
    ROW_LIMIT_MAX = 50000
    
    @classmethod
    def is_api_key_configured(cls) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY.startswith("sk-"))
    
    @classmethod
    def validate_config(cls) -> Tuple[bool, List[str]]:
        """Validate configuration and return issues."""
        issues = []
        
        if not cls.is_api_key_configured():
            issues.append("OpenAI API key is not configured or invalid")
        
        if cls.ROW_LIMIT_DEFAULT <= 0:
            issues.append("Row limit default must be positive")
        
        if cls.ROW_LIMIT_DEFAULT > cls.ROW_LIMIT_MAX:
            issues.append(f"Row limit default cannot exceed maximum ({cls.ROW_LIMIT_MAX})")
        
        return len(issues) == 0, issues
    
    @classmethod
    def reload_config(cls):
        """Reload configuration from environment."""
        load_dotenv(override=True)
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        cls.ROW_LIMIT_DEFAULT = int(os.getenv("ROW_LIMIT_DEFAULT", "1000"))

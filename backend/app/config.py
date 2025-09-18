from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Core
    PROJECT_NAME: str = "F-Ops"
    API_V1_STR: str = "/api/v1"

    # Local Storage (no Postgres)
    SQLITE_URL: str = "sqlite:///./fops.db"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    AUDIT_LOG_DIR: str = "./audit_logs"

    # MCP Servers (local)
    MCP_GITHUB_TOKEN: str = ""
    MCP_GITLAB_TOKEN: str = ""

    # AI/ML
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_MODEL: str = "gpt-4"

    # Security
    ALLOWED_REPOS: List[str] = []  # Allow-listed repos
    SCOPED_NAMESPACES: List[str] = []
    SECRET_KEY: str = "your-secret-key-here-change-in-production"

    # CORS (local-first)
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields for Phase 1
    }

settings = Settings()
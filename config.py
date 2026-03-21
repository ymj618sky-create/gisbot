"""
Configuration Settings for GIS Agent

Loads settings from environment variables and provides a unified interface.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""

    # Anthropic Settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Application Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Workspace Settings
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", str(Path.cwd()))
    DATA_DIR: str = os.getenv("DATA_DIR", str(Path.cwd() / "data"))

    # Agent Settings
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "15"))
    MEMORY_WINDOW: int = int(os.getenv("MEMORY_WINDOW", "50"))

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


# Global settings instance
settings = Settings()
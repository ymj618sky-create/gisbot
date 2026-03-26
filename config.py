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
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # 阿里云百炼（Dashscope）Settings
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen3.5-plus")
    # Coding Plan 专属 Base URL（兼容 OpenAI 协议）
    DASHSCOPE_BASE_URL: str = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://coding.dashscope.aliyuncs.com/v1"
    )

    # 默认 Provider 设置
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "dashscope")

    # Application Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Workspace Settings
    WORKSPACE_DIR: str = os.getenv("WORKSPACE_DIR", str(Path.cwd() / "workspace"))
    DATA_DIR: str = os.getenv("DATA_DIR", str(Path.cwd() / "workspace" / "data"))

    # Resolve to absolute paths
    @property
    def workspace_path(self) -> Path:
        """Get workspace as absolute Path."""
        return Path(self.WORKSPACE_DIR).resolve()

    @property
    def data_path(self) -> Path:
        """Get data directory as absolute Path."""
        return Path(self.DATA_DIR).resolve()

    # Agent Settings
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "100"))
    MEMORY_WINDOW: int = int(os.getenv("MEMORY_WINDOW", "50"))

    # Python Settings
    ARCGIS_PRO_PYTHON: str = os.getenv("ARCGIS_PRO_PYTHON", "python")

    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


# Global settings instance
settings = Settings()
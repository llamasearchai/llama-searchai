"""
Settings configuration module for LlamaSearch AI.

This module uses Pydantic to define and validate configuration settings
loaded from environment variables or .env files.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseSettings, Field, root_validator, validator

# Define the project base directory
BASE_DIR = Path(__file__).parent.parent.parent


class LlamaSearchSettings(BaseSettings):
    """Settings for the LlamaSearch AI platform."""

    # API and Service Configuration
    API_HOST: str = Field(default="0.0.0.0", env="LLAMASEARCH_API_HOST")
    API_PORT: int = Field(default=8000, env="LLAMASEARCH_API_PORT")
    API_WORKERS: int = Field(default=4, env="LLAMASEARCH_API_WORKERS")
    DEBUG: bool = Field(default=False, env="LLAMASEARCH_DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LLAMASEARCH_LOG_LEVEL")

    # Security
    SECRET_KEY: str = Field(
        default="super-secret-key-change-in-production", env="LLAMASEARCH_SECRET_KEY"
    )
    API_KEY_HEADER: str = Field(default="X-API-Key", env="LLAMASEARCH_API_KEY_HEADER")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="LLAMASEARCH_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="LLAMASEARCH_ALLOWED_HOSTS")
    CORS_ORIGINS: List[str] = Field(default=["*"], env="LLAMASEARCH_CORS_ORIGINS")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///llamasearch.db", env="LLAMASEARCH_DATABASE_URL"
    )
    REDIS_URL: Optional[str] = Field(default=None, env="LLAMASEARCH_REDIS_URL")

    # AI/ML
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    DEFAULT_MODEL: str = Field(default="gpt-3.5-turbo", env="LLAMASEARCH_DEFAULT_MODEL")

    # Metasearch
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GOOGLE_CX: Optional[str] = Field(default=None, env="GOOGLE_CX")
    BING_API_KEY: Optional[str] = Field(default=None, env="BING_API_KEY")

    # Vector DB
    VECTOR_DB_URL: Optional[str] = Field(default=None, env="LLAMASEARCH_VECTOR_DB_URL")
    VECTOR_DB_TYPE: str = Field(default="qdrant", env="LLAMASEARCH_VECTOR_DB_TYPE")

    # Personalization
    PERSONALIZATION_ENABLED: bool = Field(
        default=True, env="LLAMASEARCH_PERSONALIZATION_ENABLED"
    )
    PRIVACY_LEVEL: str = Field(default="high", env="LLAMASEARCH_PRIVACY_LEVEL")

    # MLX Support
    USE_MLX: bool = Field(default=False, env="LLAMASEARCH_USE_MLX")

    # Storage
    STORAGE_DIR: str = Field(
        default=str(BASE_DIR / "storage"), env="LLAMASEARCH_STORAGE_DIR"
    )

    # Dashboard
    DASHBOARD_HOST: str = Field(default="0.0.0.0", env="LLAMASEARCH_DASHBOARD_HOST")
    DASHBOARD_PORT: int = Field(default=8050, env="LLAMASEARCH_DASHBOARD_PORT")

    # Feature Flags
    FEATURES: Dict[str, bool] = Field(
        default={
            "metasearch": True,
            "vector": True,
            "personalization": True,
            "blockchain": False,
            "voice": False,
            "monitor": True,
            "scheduler": True,
            "notifications": True,
            "backup": True,
            "simulator": False,
        },
        env="LLAMASEARCH_FEATURES",
    )

    class Config:
        """Pydantic config for settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate that LOG_LEVEL is a valid logging level."""
        allowed_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        if v.upper() not in allowed_levels:
            logger.warning(f"Invalid log level: {v}. Defaulting to INFO.")
            return "INFO"
        return v.upper()

    @validator("PRIVACY_LEVEL")
    def validate_privacy_level(cls, v: str) -> str:
        """Validate that PRIVACY_LEVEL is valid."""
        allowed_levels = ["low", "medium", "high", "max"]
        if v.lower() not in allowed_levels:
            logger.warning(f"Invalid privacy level: {v}. Defaulting to high.")
            return "high"
        return v.lower()

    @validator("VECTOR_DB_TYPE")
    def validate_vector_db_type(cls, v: str) -> str:
        """Validate that VECTOR_DB_TYPE is supported."""
        allowed_types = [
            "qdrant",
            "milvus",
            "weaviate",
            "pinecone",
            "faiss",
            "elasticsearch",
        ]
        if v.lower() not in allowed_types:
            logger.warning(f"Invalid vector DB type: {v}. Defaulting to qdrant.")
            return "qdrant"
        return v.lower()

    @root_validator
    def validate_api_keys(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Check if at least one search API key is provided when metasearch is enabled."""
        features = values.get("FEATURES", {})

        if features.get("metasearch", True) and not any(
            [values.get("GOOGLE_API_KEY"), values.get("BING_API_KEY")]
        ):
            logger.warning(
                "Metasearch is enabled but no search API keys are provided. "
                "Set GOOGLE_API_KEY, BING_API_KEY, or disable metasearch."
            )

        if features.get("personalization", True) and not values.get("REDIS_URL"):
            logger.warning(
                "Personalization is enabled but no Redis URL is provided. "
                "Some personalization features may be limited."
            )

        # Create storage directory if it doesn't exist
        storage_dir = values.get("STORAGE_DIR")
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)

        return values


# Create the settings instance
settings = LlamaSearchSettings()

# Configure Loguru logger
logger.remove()
logger.add(
    sink=lambda msg: print(msg),
    level=settings.LOG_LEVEL,
    colorize=True,
    backtrace=settings.DEBUG,
    diagnose=settings.DEBUG,
)

if settings.DEBUG:
    logger.debug("Starting in DEBUG mode")
    logger.debug(f"Settings: {settings.dict()}")
else:
    # Only log non-sensitive settings in production
    safe_settings = settings.dict(
        exclude={"SECRET_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "BING_API_KEY"}
    )
    logger.info(f"Loading settings: {safe_settings}")

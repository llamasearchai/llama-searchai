"""
Main entry point for the LlamaSearch AI API.
"""

import uvicorn
from llamasearchai.config.settings import settings
from loguru import logger


def main():
    """
    Run the LlamaSearch AI API server.
    """
    logger.info(
        f"Starting LlamaSearch AI API on {settings.API_HOST}:{settings.API_PORT}"
    )

    uvicorn.run(
        "llamasearchai.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()

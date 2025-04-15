"""
LlamaSearch AI: Unified AI Platform

This is the main package for LlamaSearch AI, a unified platform that provides access
to multiple specialized AI capabilities through a consistent interface.
"""

__version__ = "0.1.0"

from llamasearchai.client import Client
from llamasearchai.config import settings

__all__ = ["Client", "settings", "__version__"]

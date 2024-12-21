# File: /backend/__init__.py

from fastapi import FastAPI
from .config.settings import get_settings

__version__ = "1.0.0"
settings = get_settings()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    from .app import app
    return app
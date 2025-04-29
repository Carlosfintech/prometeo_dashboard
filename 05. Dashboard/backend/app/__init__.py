"""
Paquete principal de la aplicación FastAPI
"""
from .api import app
from .ml_service import THRESHOLD

__all__ = ["app", "THRESHOLD"] 
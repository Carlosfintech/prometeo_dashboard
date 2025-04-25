"""
Re-export de generate_features desde el módulo original en 03.Modelo
"""
from src.features.pipeline_featureengineering_func import generate_features

__all__ = ["generate_features"] 
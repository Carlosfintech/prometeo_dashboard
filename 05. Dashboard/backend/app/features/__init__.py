"""
Re-export de generate_features desde el módulo local pipeline_featureengineering_func
"""
from app.features.pipeline_featureengineering_func import generate_features

__all__ = ["generate_features"] 
# File: /backend/pipelines/__init__.py

from .image_pipeline import JewelryImagePipeline
from .items import ProductItem

__all__ = ['JewelryImagePipeline', 'ProductItem']
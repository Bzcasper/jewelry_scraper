# File: /backend/database/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Product(Base):
    """Core product model for storing scraped jewelry data"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    external_id = Column(String(50), unique=True, nullable=True)  # Platform-specific ID (e.g., ASIN)
    
    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), unique=True, nullable=False)
    
    # Price info
    price_amount = Column(Float, nullable=False)
    price_currency = Column(String(3), default='USD')
    original_price = Column(Float, nullable=True)  # For tracking discounts
    
    # Classification
    platform = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    
    # Seller info
    seller_id = Column(String(100), nullable=True)
    seller_name = Column(String(200), nullable=True)
    seller_rating = Column(Float, nullable=True)
    
    # Product details
    specifications = Column(JSON, nullable=True)  # Flexible product attributes
    material = Column(String(100), nullable=True)
    weight = Column(String(50), nullable=True)  # Store as string to handle different units
    dimensions = Column(String(100), nullable=True)
    
    # Timestamps
    date_scraped = Column(DateTime, default=datetime.utcnow)
    date_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_price_check = Column(DateTime, nullable=True)
    
    # Status and flags
    is_available = Column(Boolean, default=True)
    is_prime = Column(Boolean, default=False)  # Amazon-specific
    stock_status = Column(String(50), nullable=True)
    
    # Relationships
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert product to dictionary representation"""
        return {
            'id': self.id,
            'title': self.title,
            'price': {
                'amount': self.price_amount,
                'currency': self.price_currency,
                'original': self.original_price
            },
            'url': self.url,
            'platform': self.platform,
            'category': self.category,
            'brand': self.brand,
            'specifications': json.loads(self.specifications) if isinstance(self.specifications, str) else self.specifications,
            'seller': {
                'name': self.seller_name,
                'rating': self.seller_rating
            },
            'images': [img.url for img in self.images],
            'date_scraped': self.date_scraped.isoformat() if self.date_scraped else None,
            'is_available': self.is_available,
            'stock_status': self.stock_status
        }

class ProductImage(Base):
    """Store product images with metadata"""
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    url = Column(String(1000), nullable=False)
    local_path = Column(String(500), nullable=True)  # Path to stored image if downloaded
    checksum = Column(String(64), nullable=True)  # For deduplication
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    is_primary = Column(Boolean, default=False)
    is_downloaded = Column(Boolean, default=False)
    
    product = relationship("Product", back_populates="images")

class PriceHistory(Base):
    """Track price changes over time"""
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    price_amount = Column(Float, nullable=False)
    price_currency = Column(String(3), default='USD')
    date_checked = Column(DateTime, default=datetime.utcnow)
    is_sale = Column(Boolean, default=False)
    
    product = relationship("Product", back_populates="price_history")
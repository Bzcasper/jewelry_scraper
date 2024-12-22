from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from typing import List, Dict
import logging

Base = declarative_base()

class Product(Base):
    """Product model for storing scraped jewelry data"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price_amount = Column(Float)
    price_currency = Column(String(3))
    description = Column(String)
    product_url = Column(String, unique=True)
    platform = Column(String)
    category = Column(String)
    brand = Column(String)
    specifications = Column(JSON)
    images = relationship("ProductImage", back_populates="product")
    seller_info = Column(JSON)
    date_scraped = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    structured_data = Column(JSON)

    def to_dict(self) -> Dict:
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'price': {
                'amount': self.price_amount,
                'currency': self.price_currency
            },
            'description': self.description,
            'product_url': self.product_url,
            'platform': self.platform,
            'category': self.category,
            'brand': self.brand,
            'specifications': self.specifications,
            'images': [img.url for img in self.images],
            'seller_info': self.seller_info,
            'date_scraped': self.date_scraped.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }

class ProductImage(Base):
    """Model for storing product images"""
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    url = Column(String, nullable=False)
    local_path = Column(String)
    is_primary = Column(Boolean, default=False)
    product = relationship("Product", back_populates="images")

class DatabaseManager:
    """Manager class for database operations"""
    def __init__(self, db_url: str = 'sqlite:///jewelry_scraper.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_product(self, product_data: Dict) -> Optional[int]:
        """Add or update a product in the database"""
        session = self.Session()
        try:
            # Check for existing product
            existing = session.query(Product).filter_by(
                product_url=product_data['product_url']
            ).first()

            if existing:
                # Update existing product
                for key, value in product_data.items():
                    if key == 'images':
                        continue
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                product = existing
            else:
                # Create new product
                images = product_data.pop('images', [])
                product = Product(**product_data)
                session.add(product)
                session.flush()  # Get product ID

                # Add images
                for img_url in images:
                    image = ProductImage(
                        product_id=product.id,
                        url=img_url,
                        is_primary=img_url == images[0]
                    )
                    session.add(image)

            session.commit()
            return product.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding product: {e}")
            return None
        finally:
            session.close()

    def get_products(
        self,
        filters: Dict = None,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = 'date_scraped',
        sort_desc: bool = True
    ) -> tuple:
        """Get products with filtering and pagination"""
        session = self.Session()
        try:
            query = session.query(Product)

            # Apply filters
            if filters:
                if price_min := filters.get('price_min'):
                    query = query.filter(Product.price_amount >= float(price_min))
                if price_max := filters.get('price_max'):
                    query = query.filter(Product.price_amount <= float(price_max))
                if platform := filters.get('platform'):
                    query = query.filter(Product.platform == platform)
                if category := filters.get('category'):
                    query = query.filter(Product.category == category)
                if search := filters.get('search'):
                    query = query.filter(Product.title.ilike(f'%{search}%'))

            # Apply sorting
            sort_col = getattr(Product, sort_by)
            query = query.order_by(sort_col.desc() if sort_desc else sort_col)

            # Get total count
            total = query.count()

            # Apply pagination
            query = query.offset((page - 1) * per_page).limit(per_page)

            products = [p.to_dict() for p in query.all()]
            return products, total

        except Exception as e:
            logging.error(f"Error fetching products: {e}")
            return [], 0
        finally:
            session.close()
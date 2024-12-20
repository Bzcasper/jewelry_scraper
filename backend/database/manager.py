from sqlalchemy import create_engine, text, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Dict, List, Tuple, Optional
import logging
import json
from datetime import datetime
import asyncio
from .models import Base, Product, ProductImage, ScrapingJob
from utils.validators import validate_product_data

class DatabaseManager:
    def __init__(self, db_url: str = 'sqlite:///jewelry_scraper.db'):
        # Initialize database engine
        self.engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
        # Setup logging
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()

    async def add_product(self, data: Dict) -> Optional[int]:
        """Add or update a product in the database"""
        try:
            # Validate product data
            if not validate_product_data(data):
                raise ValueError("Invalid product data")

            with self.session_scope() as session:
                # Check for existing product
                existing = session.query(Product).filter_by(
                    platform=data['platform'],
                    external_id=data['external_id']
                ).first()

                if existing:
                    # Update existing product
                    for key, value in data.items():
                        if key != 'images':
                            setattr(existing, key, value)
                    product = existing
                else:
                    # Create new product
                    images = data.pop('images', [])
                    product = Product(**data)
                    session.add(product)
                    session.flush()  # Get product ID

                    # Add images
                    for img_data in images:
                        image = ProductImage(
                            product_id=product.id,
                            url=img_data['url'],
                            local_path=img_data.get('local_path'),
                            is_primary=img_data.get('is_primary', False)
                        )
                        session.add(image)

                session.commit()
                return product.id

        except Exception as e:
            self.logger.error(f"Error adding product: {str(e)}")
            return None

    async def get_products(
        self,
        filters: Dict = None,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = 'date_scraped',
        sort_desc: bool = True
    ) -> Tuple[List[Dict], int]:
        """Get products with filtering and pagination"""
        try:
            with self.session_scope() as session:
                query = session.query(Product)

                # Apply filters
                if filters:
                    query = self._apply_filters(query, filters)

                # Get total count
                total = query.count()

                # Apply sorting
                query = self._apply_sorting(query, sort_by, sort_desc)

                # Apply pagination
                query = query.offset((page - 1) * per_page).limit(per_page)

                # Execute query and format results
                products = [self._format_product(p) for p in query.all()]
                return products, total

        except Exception as e:
            self.logger.error(f"Error fetching products: {str(e)}")
            return [], 0

    def _apply_filters(self, query, filters: Dict):
        """Apply filters to query"""
        if price_min := filters.get('price_min'):
            query = query.filter(Product.price_amount >= float(price_min))
        
        if price_max := filters.get('price_max'):
            query = query.filter(Product.price_amount <= float(price_max))
        
        if platform := filters.get('platform'):
            query = query.filter(Product.platform == platform)
        
        if category := filters.get('category'):
            query = query.filter(Product.category == category)
        
        if search := filters.get('search'):
            search_term = f"%{search}%"
            query = query.filter(Product.title.ilike(search_term))
        
        if date_from := filters.get('date_from'):
            query = query.filter(Product.date_scraped >= date_from)
        
        if date_to := filters.get('date_to'):
            query = query.filter(Product.date_scraped <= date_to)

        return query

    def _apply_sorting(self, query, sort_by: str, desc: bool = True):
        """Apply sorting to query"""
        sort_field = getattr(Product, sort_by, Product.date_scraped)
        return query.order_by(desc(sort_field) if desc else sort_field)

    def _format_product(self, product: Product) -> Dict:
        """Format product for API response"""
        return {
            'id': product.id,
            'title': product.title,
            'price': {
                'amount': float(product.price_amount),
                'currency': product.price_currency
            },
            'description': product.description,
            'platform': product.platform,
            'category': product.category,
            'brand': product.brand,
            'specifications': product.specifications,
            'images': [
                {
                    'url': img.url,
                    'local_path': img.local_path,
                    'is_primary': img.is_primary
                }
                for img in product.images
            ],
            'seller_info': product.seller_info,
            'date_scraped': product.date_scraped.isoformat(),
            'last_updated': product.last_updated.isoformat()
        }

    async def delete_products(self, ids: List[int]) -> bool:
        """Delete products by IDs"""
        try:
            with self.session_scope() as session:
                # Delete associated images first
                session.query(ProductImage).filter(
                    ProductImage.product_id.in_(ids)
                ).delete(synchronize_session=False)
                
                # Delete products
                deleted = session.query(Product).filter(
                    Product.id.in_(ids)
                ).delete(synchronize_session=False)
                
                return deleted > 0

        except Exception as e:
            self.logger.error(f"Error deleting products: {str(e)}")
            return False

    async def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self.session_scope() as session:
                return {
                    'total_products': session.query(Product).count(),
                    'platforms': self._get_platform_stats(session),
                    'categories': self._get_category_stats(session),
                    'price_stats': self._get_price_stats(session),
                    'recent_activity': self._get_activity_stats(session)
                }

        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {}

    def _get_platform_stats(self, session) -> Dict:
        """Get statistics by platform"""
        result = session.query(
            Product.platform,
            func.count(Product.id).label('count'),
            func.avg(Product.price_amount).label('avg_price')
        ).group_by(Product.platform).all()
        
        return {
            row.platform: {
                'count': row.count,
                'avg_price': float(row.avg_price)
            }
            for row in result
        }

    async def optimize(self):
        """Perform database optimization"""
        try:
            with self.session_scope() as session:
                # Vacuum database
                session.execute(text('VACUUM'))
                
                # Analyze tables
                session.execute(text('ANALYZE'))
                
                # Clean old data
                self._clean_old_data(session)
                
                self.logger.info("Database optimization completed")

        except Exception as e:
            self.logger.error(f"Error optimizing database: {str(e)}")

    def _clean_old_data(self, session):
        """Clean up old or invalid data"""
        # Remove products without images
        session.query(Product).filter(
            ~Product.images.any()
        ).delete(synchronize_session=False)
        
        # Remove orphaned images
        session.query(ProductImage).filter(
            ~ProductImage.product_id.in_(
                session.query(Product.id)
            )
        ).delete(synchronize_session=False)
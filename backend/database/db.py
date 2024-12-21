import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Union
from contextlib import contextmanager
import json
from dataclasses import dataclass
from decimal import Decimal
import threading
import queue
from pathlib import Path
from backend.utils.logger import log_error, log_critical_error

@dataclass
class ProductData:
    """Product data structure with validation"""
    title: str
    price: Union[float, str, Decimal]
    description: Optional[str] = None
    image_urls: List[str] = None
    product_url: Optional[str] = None
    category: Optional[str] = None
    platform: str = "unknown"
    asin: Optional[str] = None
    seller: Optional[Dict] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    features: List[str] = None
    technical_details: Dict = None
    specifications: Dict = None
    shipping_info: Optional[str] = None
    prime_eligible: bool = False
    currency: str = "USD"
    date_scraped: str = None

class DatabaseConfig:
    DB_NAME = "products.db"
    QUEUE_SIZE = 1000
    BATCH_SIZE = 50
    MAX_RETRIES = 3
    TIMEOUT = 30

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize database manager"""
        self.insert_queue = queue.Queue(maxsize=DatabaseConfig.QUEUE_SIZE)
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        self._ensure_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(
            DatabaseConfig.DB_NAME,
            timeout=DatabaseConfig.TIMEOUT,
            isolation_level='IMMEDIATE'
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_database(self):
        """Ensure database and tables exist with proper schema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create products table with enhanced schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        price DECIMAL(10,2),
                        description TEXT,
                        image_urls TEXT,
                        product_url TEXT,
                        category TEXT,
                        platform TEXT NOT NULL,
                        asin TEXT,
                        seller_info TEXT,
                        rating FLOAT,
                        review_count INTEGER,
                        features TEXT,
                        technical_details TEXT,
                        specifications TEXT,
                        shipping_info TEXT,
                        prime_eligible BOOLEAN,
                        currency TEXT,
                        date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, asin)
                    )
                """)
                
                # Create indices for common queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_platform_category 
                    ON products(platform, category)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_date_scraped 
                    ON products(date_scraped)
                """)
                
                # Create scraping jobs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT UNIQUE NOT NULL,
                        status TEXT NOT NULL,
                        query TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        items_scraped INTEGER DEFAULT 0,
                        error TEXT
                    )
                """)
                
                conn.commit()
                logging.info("Database initialized successfully")
                
        except Exception as e:
            log_critical_error(f"Failed to initialize database: {e}")
            raise

    def _process_queue(self):
        """Process queued product insertions in batches"""
        batch = []
        while True:
            try:
                # Collect batch of products
                while len(batch) < DatabaseConfig.BATCH_SIZE:
                    try:
                        product = self.insert_queue.get(timeout=1)
                        batch.append(product)
                    except queue.Empty:
                        break
                
                if batch:
                    self._batch_insert(batch)
                    batch = []
                    
            except Exception as e:
                log_error(f"Error processing database queue: {e}")
                
    def _batch_insert(self, products: List[ProductData]):
        """Insert multiple products in a single transaction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany("""
                    INSERT OR REPLACE INTO products (
                        title, price, description, image_urls, product_url,
                        category, platform, asin, seller_info, rating,
                        review_count, features, technical_details,
                        specifications, shipping_info, prime_eligible,
                        currency, date_scraped
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [self._prepare_product_data(p) for p in products])
                
                conn.commit()
                logging.debug(f"Batch inserted {len(products)} products")
                
            except Exception as e:
                log_error(f"Error in batch insert: {e}")
                raise

    def add_product(self, product: Dict):
        """Add a product to the insertion queue"""
        try:
            product_data = ProductData(
                title=product.get('title', ''),
                price=product.get('price', 0),
                description=product.get('description'),
                image_urls=product.get('image_urls', []),
                product_url=product.get('product_url'),
                category=product.get('category'),
                platform=product.get('platform', 'unknown'),
                asin=product.get('asin'),
                seller=product.get('seller'),
                rating=product.get('rating'),
                review_count=product.get('review_count'),
                features=product.get('features', []),
                technical_details=product.get('technical_details', {}),
                shipping_info=product.get('shipping_info'),
                prime_eligible=product.get('prime_eligible', False),
                currency=product.get('currency', 'USD'),
                date_scraped=datetime.now().isoformat()
            )
            self.insert_queue.put(product_data)
            
        except Exception as e:
            log_error(f"Error queuing product: {e}")

    def _prepare_product_data(self, product: ProductData) -> tuple:
        """Prepare product data for database insertion"""
        return (
            product.title,
            str(product.price),
            product.description,
            ','.join(product.image_urls) if product.image_urls else None,
            product.product_url,
            product.category,
            product.platform,
            product.asin,
            json.dumps(product.seller) if product.seller else None,
            product.rating,
            product.review_count,
            json.dumps(product.features) if product.features else None,
            json.dumps(product.technical_details) if product.technical_details else None,
            json.dumps(product.specifications) if product.specifications else None,
            product.shipping_info,
            product.prime_eligible,
            product.currency,
            product.date_scraped or datetime.now().isoformat()
        )

    def fetch_products(self, filters: Optional[Dict] = None, page: int = 1, per_page: int = 50) -> tuple:
        """Fetch products with filtering and pagination"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM products WHERE 1=1"
                params = []
                
                if filters:
                    if platform := filters.get('platform'):
                        query += " AND platform = ?"
                        params.append(platform)
                    
                    if category := filters.get('category'):
                        query += " AND category = ?"
                        params.append(category)
                    
                    if min_price := filters.get('price_min'):
                        query += " AND CAST(price AS DECIMAL) >= ?"
                        params.append(min_price)
                    
                    if max_price := filters.get('price_max'):
                        query += " AND CAST(price AS DECIMAL) <= ?"
                        params.append(max_price)
                
                # Count total results
                count_cursor = conn.cursor()
                count_cursor.execute(f"SELECT COUNT(*) FROM ({query})", params)
                total_count = count_cursor.fetchone()[0]
                
                # Add pagination
                query += " ORDER BY date_scraped DESC LIMIT ? OFFSET ?"
                params.extend([per_page, (page - 1) * per_page])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_dict(row) for row in rows], total_count
                
        except Exception as e:
            log_error(f"Error fetching products: {e}")
            return [], 0

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert database row to dictionary"""
        data = dict(row)
        
        # Parse JSON fields
        for field in ['seller_info', 'features', 'technical_details', 'specifications']:
            if data.get(field):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = None
        
        # Parse image URLs
        if data.get('image_urls'):
            data['image_urls'] = data['image_urls'].split(',')
        else:
            data['image_urls'] = []
            
        return data

# Initialize database manager
db_manager = DatabaseManager()

# Expose simplified interface for backward compatibility
def initialize_db():
    """Initialize database for backward compatibility"""
    db_manager._ensure_database()

def add_product(product: Dict):
    """Add product for backward compatibility"""
    db_manager.add_product(product)

def fetch_all_products():
    """Fetch all products for backward compatibility"""
    products, _ = db_manager.fetch_products()
    return products
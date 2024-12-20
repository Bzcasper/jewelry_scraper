import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Product
from database.manager import DatabaseManager
import datetime

@pytest.fixture
def db_manager():
    """Initialize test database"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return DatabaseManager(session_factory=Session)

@pytest.fixture
def sample_product():
    """Create sample product data"""
    return {
        'title': 'Test Ring',
        'price_amount': 99.99,
        'price_currency': 'USD',
        'description': 'A beautiful test ring',
        'platform': 'ebay',
        'category': 'rings',
        'images': ['http://example.com/image.jpg']
    }

class TestDatabaseOperations:
    def test_add_product(self, db_manager, sample_product):
        product_id = db_manager.add_product(sample_product)
        assert product_id is not None
        
        product = db_manager.get_product(product_id)
        assert product.title == sample_product['title']
        assert float(product.price_amount) == sample_product['price_amount']

    def test_get_products_with_filters(self, db_manager, sample_product):
        db_manager.add_product(sample_product)
        
        filters = {
            'platform': 'ebay',
            'category': 'rings',
            'price_min': 50,
            'price_max': 150
        }
        
        products = db_manager.get_products(filters=filters)
        assert len(products) == 1
        assert products[0].title == sample_product['title']

    def test_update_product(self, db_manager, sample_product):
        product_id = db_manager.add_product(sample_product)
        
        updates = {
            'price_amount': 149.99,
            'description': 'Updated description'
        }
        
        success = db_manager.update_product(product_id, updates)
        assert success
        
        product = db_manager.get_product(product_id)
        assert float(product.price_amount) == updates['price_amount']
        assert product.description == updates['description']

    def test_delete_product(self, db_manager, sample_product):
        product_id = db_manager.add_product(sample_product)
        success = db_manager.delete_product(product_id)
        assert success
        
        product = db_manager.get_product(product_id)
        assert product is None
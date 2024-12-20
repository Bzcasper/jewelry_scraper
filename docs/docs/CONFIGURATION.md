

Configuration Guide
Proper configuration is essential for the Jewelry Scraper application to function correctly. This guide provides detailed instructions on setting up and customizing various configuration options.

Table of Contents
Environment Variables
Scraping Settings
Image Processing Options
Proxy Configuration
Database Configuration
Caching Strategy
Advanced Settings
1. Environment Variables
Environment variables are managed using a .env file located in the root directory. Here's a breakdown of the key variables:

env
# API Configuration
FLASK_APP=app.py
FLASK_ENV=development
PORT=5000

# Scraping Configuration
MAX_CONCURRENT_REQUESTS=8
DOWNLOAD_DELAY=2
ROTATING_PROXY_LIST_PATH=proxies.txt

# Database Configuration
DATABASE_URL=sqlite:///jewelry_scraper.db

# Image Storage
IMAGE_STORAGE_PATH=product_images
MAX_IMAGE_SIZE=1200

# Caching Configuration
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=300
Setting Up the .env File
Create the .env File:

bash
cp .env.example .env
Edit the .env File: Open the .env file in a text editor and adjust the variables as needed.

2. Scraping Settings
Customize the scraping behavior by modifying the config/scraping.py file.

python
# config/scraping.py

SCRAPING_CONFIG = {
    'ebay': {
        'max_items_per_search': 100,
        'search_delay': 2.0,
        'retry_attempts': 3,
        'categories': [
            'Rings',
            'Necklaces',
            'Bracelets',
            'Earrings'
        ]
    },
    'amazon': {
        'max_items_per_search': 100,
        'search_delay': 2.5,
        'retry_attempts': 3,
        'categories': [
            'Jewelry',
            'Fine Jewelry',
            'Fashion Jewelry'
        ]
    }
}
Key Parameters
max_items_per_search: Maximum number of items to scrape per search query.
search_delay: Delay (in seconds) between search requests to prevent overloading the server.
retry_attempts: Number of retry attempts for failed requests.
categories: List of jewelry categories to scrape.
3. Image Processing Options
Configure image handling by editing config/image_processing.py.


# config/image_processing.py

IMAGE_CONFIG = {
    'max_dimension': 1200,        # Maximum width or height in pixels
    'quality': 85,                 # Image quality (1-100)
    'format': 'JPEG',              # Image format (JPEG, PNG, etc.)
    'thumbnails': {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600)
    }
}
Options Explained
max_dimension: Limits the size of the largest dimension (width or height) of the image.
quality: Determines the compression quality of the image.
format: Specifies the output image format.
thumbnails: Defines sizes for generating thumbnail images.
4. Proxy Configuration
Enhance scraping resilience by setting up proxy rotation.

Setting Up Proxies
Create proxies.txt: Place your proxy list in the config/proxies.txt file, one proxy per line.


http://proxy1.example.com:8080
http://proxy2.example.com:8080
http://proxy3.example.com:8080
Configure Proxy Rotation: Ensure the ROTATING_PROXY_LIST_PATH in the .env file points to config/proxies.txt.

Proxy Manager
The scraper/utils/proxy_manager.py handles proxy rotation and management. Customize its behavior if needed.

5. Database Configuration
The application uses SQLite by default, but you can switch to PostgreSQL or another database system.

SQLite Configuration

DATABASE_URL=sqlite:///jewelry_scraper.db
PostgreSQL Configuration
env
Copy code
DATABASE_URL=postgresql://username:password@localhost:5432/jewelry_scraper
Setting Up PostgreSQL
Install PostgreSQL: Follow the installation guide for your operating system.

Create Database and User:

CREATE DATABASE jewelry_scraper;
CREATE USER yourusername WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE jewelry_scraper TO yourusername;
Update .env File: Replace the DATABASE_URL with your PostgreSQL connection string.

6. Caching Strategy
Implement caching to improve performance for frequent queries.

Redis Caching
Configure Redis as the caching backend.

env
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=300
Cache Configuration File
Modify config/cache.py if additional caching configurations are needed.

7. Advanced Settings
Rate Limiting
Adjust rate limiting settings to control the flow of requests.

python
# scraper/utils/rate_limiter.py

RATE_LIMIT_CONFIG = {
    'requests_per_minute': 60,
    'burst': 10
}
Logging Configuration
Customize logging behavior in backend/logger.py.

python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
Scheduler Settings
If using a scheduler for automated tasks, configure it in backend/scheduler.py.


# Example using APScheduler

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(func=backup_database, trigger="interval", hours=24)
scheduler.start()
Conclusion
Proper configuration ensures the Jewelry Scraper operates efficiently and reliably. Always double-check your settings and consult the relevant sections of this guide when making changes.

For further assistance, refer to the Troubleshooting Guide or contact the support team. 

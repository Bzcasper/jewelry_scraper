# jewelry_scraper

A full-stack application to scrape jewelry products from eBay and Amazon using Scrapy, Flask, and React.

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Pipelines](#pipelines)
- [Testing](#testing)
- [Advanced Features](#advanced-features)
- [License](#license)

## Setup Instructions

1. **Clone the Repository:**
    `ash
    git clone https://github.com/yourusername/jewelry_scraper.git
    cd jewelry_scraper
    `

2. **Set Up Backend Environment:**
    - **Using Conda:**
        `ash
        conda create -n jewelry_env python=3.10 -y
        conda activate jewelry_env
        `
    - **Using Virtualenv:**
        `ash
        python -m venv jewelry_env
        # Windows
        .\jewelry_env\Scripts\activate
        # Unix or MacOS
        source ./jewelry_env/bin/activate
        `

3. **Install Backend Dependencies:**
    `ash
    pip install -r backend/requirements.txt
    `

4. **Set Up Frontend:**
    `ash
    cd frontend
    npm install
    cd ..
    `

5. **Run the Application:**
    - **Start Flask Backend:**
        `ash
        cd backend
        python app.py
        `
    - **Start React Frontend:**
        Open a new terminal window/tab and run:
        `ash
        cd frontend
        npm start
        `
    - **Access the Application:**
        Open your browser and navigate to http://localhost:3000 to interact with the React frontend.

## Project Structure

jewelry_scraper/  
│  
├── backend/  
│   ├── app.py  
│   ├── scraper/  
│   │   ├── __init__.py  
│   │   ├── ebay_spider.py  
│   │   ├── amazon_spider.py  
│   │   └── selenium_utils.py  
│   ├── database/  
│   │   ├── __init__.py  
│   │   ├── db.py  
│   │   └── backup.py  
│   ├── logs/  
│   ├── tests/  
│   │   ├── __init__.py  
│   │   └── test_spiders.py  
│   ├── requirements.txt  
│   └── logger.py  
│  
├── frontend/  
│   ├── package.json  
│   ├── public/  
│   │   └── index.html  
│   └── src/  
│       ├── App.js  
│       ├── index.js  
│       └── components/  
│           ├── SearchBar.js  
│           ├── DataTable.js  
│           ├── DataDashboard.js  
│           └── EnhancedSearch.js  
│  
├── db_backups/  
├── .github/  
│   └── workflows/  
│       └── python-app.yml  
├── .gitignore  
└── README.md

## Usage

1. **Scrape Products:**
    - Use the React frontend to input your search query and select the platform (eBay or Amazon).
    - Click the "Search" button to initiate scraping.
    - Scraped products will be displayed in the DataTable and DataDashboard components and stored in the SQLite database.

2. **View Scraped Data:**
    - Access the /products endpoint via the Flask backend to retrieve all scraped products.
    - Alternatively, view the data in the products.db SQLite database using any SQLite viewer.

3. **Trigger Database Backup:**
    - Access the /backup endpoint to manually trigger a database backup.
    - Backups are stored in the db_backups directory with timestamped filenames.

## Pipelines

- **DatabasePipeline:** Handles storing scraped data into the SQLite database.
- **ImagesPipeline:** Manages downloading and storing product images.

## Testing

1. **Navigate to Backend Directory:**
    `ash
    cd backend
    `

2. **Run Tests with pytest:**
    `ash
    pytest
    `

## Advanced Features

- **Proxy Rotation and User-Agent Spoofing:** Implemented in scraper/selenium_utils.py to enhance scraping resilience.
- **Error Logging and Notifications:** Configured in logger.py to log errors and send email notifications for critical issues.
- **Database Backups:** Automated backups via the /backup endpoint ensure data safety.
- **Continuous Integration:** GitHub Actions workflow (.github/workflows/python-app.yml) automates testing and linting on commits.
- **Data Visualization:** DataDashboard component provides visual insights into scraped data through charts and statistics.

## License

MIT License

# Jewelry Scraper - User Guide & Best Practices

## Table of Contents
1. [System Overview](#system-overview)
2. [Setup Guide](#setup-guide)
3. [Configuration Options](#configuration-options)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)
6. [Performance Optimization](#performance-optimization)
7. [Future Improvements](#future-improvements)

## System Overview

The Jewelry Scraper is a full-stack application designed to collect product data from eBay and Amazon. Key features include:

- Real-time product scraping
- Image downloading and optimization
- Structured data storage
- User-friendly dashboard
- Data export capabilities

### Architecture Components:

```plaintext
Frontend (React) --> API Layer (Flask) --> Scraping Engine (Scrapy/Selenium) --> Database (SQLite)
                                      --> Image Processing --> File Storage
```

## Setup Guide

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-repo/jewelry-scraper.git
cd jewelry-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
cd frontend
npm install
```

### 2. Configuration Files

Create a `.env` file in the root directory:

```env
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
```

### 3. Database Initialization

```bash
# Initialize database
python init_db.py

# Verify installation
python -m pytest tests/
```

## Configuration Options

### Scraping Settings

```python
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
```

### Image Processing Options

```python
# config/image_processing.py
IMAGE_CONFIG = {
    'max_dimension': 1200,
    'quality': 85,
    'format': 'JPEG',
    'thumbnails': {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600)
    }
}
```

## Best Practices

### 1. Scraping Strategy

```python
# Optimal scraping approach
def configure_scraping():
    return {
        'batch_size': 20,          # Items per batch
        'delay_between_batches': 5, # Seconds
        'max_retries': 3,          # Per item
        'timeout': 30,             # Seconds
        'respect_robots_txt': True
    }
```

### 2. Rate Limiting

- Use adaptive delays based on server response
- Implement exponential backoff for retries
- Rotate proxies and user agents

### 3. Image Handling

- Download images asynchronously
- Implement progressive loading
- Cache processed images
- Use WebP format when possible

### 4. Data Quality

- Validate all scraped data
- Implement deduplication
- Store raw and processed data
- Regular data cleanup

## Troubleshooting

Common issues and solutions:

1. **Blocked Requests**
   ```python
   # Implement in your spider
   def handle_blocked_request(self, response):
       if response.status == 403:
           self.rotate_proxy()
           return self.retry_request(response.request)
   ```

2. **Image Download Failures**
   ```python
   # Retry logic for images
   async def download_with_retry(self, url, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await self.download_image(url)
           except Exception as e:
               if attempt == max_retries - 1:
                   logging.error(f"Failed to download image: {url}")
                   return None
               await asyncio.sleep(2 ** attempt)
   ```

## Performance Optimization

### 1. Database Indexing

```sql
-- Add these indexes for better performance
CREATE INDEX idx_products_platform ON products(platform);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_date ON products(date_scraped);
```

### 2. Caching Strategy

```python
# Implement caching for frequent queries
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
}
```

### 3. Batch Processing

```python
# Batch processing for better performance
async def process_batch(self, items):
    async with aiohttp.ClientSession() as session:
        tasks = [self.process_item(item, session) for item in items]
        return await asyncio.gather(*tasks)
```

## Future Improvements

1. **Enhanced Data Collection**
   - Add support for more platforms
   - Implement ML for category classification
   - Add price history tracking

2. **System Scalability**
   - Migrate to PostgreSQL
   - Implement distributed scraping
   - Add Redis caching

3. **Frontend Enhancements**
   - Real-time updates
   - Advanced filtering
   - Data visualization
   - Bulk operations

4. **Monitoring & Analytics**
   - Performance metrics
   - Success rate tracking
   - Data quality metrics
   - Cost analysis

### Implementation Priorities

```python
IMPROVEMENT_PRIORITIES = {
    'high': [
        'Proxy rotation system',
        'Image optimization',
        'Error recovery'
    ],
    'medium': [
        'Data validation',
        'Caching system',
        'UI improvements'
    ],
    'low': [
        'Additional platforms',
        'Advanced analytics',
        'API extensions'
    ]
}
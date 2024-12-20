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
}```markdown
# Jewelry Scraper

A full-stack application for scraping and managing jewelry product data from major e-commerce platforms.

## Features

- Real-time product scraping from eBay and Amazon
- Advanced image processing and optimization
- Comprehensive data validation and cleaning
- Interactive dashboard with real-time updates
- Advanced search and filtering capabilities
- Data export and backup functionality
- Monitoring and alerting system

## Technology Stack

### Backend
- Python 3.10+
- FastAPI
- Scrapy
- Selenium/undetected-chromedriver
- SQLAlchemy
- PostgreSQL
- Redis

### Frontend
- React
- Tailwind CSS
- TypeScript
- Chart.js

### Infrastructure
- Docker
- Prometheus
- Grafana

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jewelry-scraper.git
cd jewelry-scraper
```

2. Set up environment:
```bash
# Copy environment template
cp .env.example .env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

3. Start services with Docker:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- API: http://localhost:5000
- Monitoring: http://localhost:3001

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
pytest tests/
```

## Configuration

Key configuration files:
- `.env`: Environment variables
- `config/settings.py`: Application settings
- `config/proxies.json`: Proxy configuration
- `docker-compose.yml`: Container configuration

## Usage

### Starting a Scraping Job

```python
from scraper import JewelryScraper

scraper = JewelryScraper()
results = await scraper.scrape(
    query="gold ring",
    platform="ebay",
    max_items=50
)
```

### API Endpoints

- `POST /scrape`: Start scraping job
- `GET /scrape/status/{job_id}`: Check job status
- `GET /products`: Get scraped products
- `GET /system/status`: Get system metrics

## Monitoring

The application includes comprehensive monitoring:

1. Metrics tracked:
   - Scraping success rate
   - Response times
   - Error rates
   - Resource usage

2. Alerting rules:
   - High error rate
   - Slow response time
   - Resource constraints

3. Dashboards:
   - System overview
   - Scraping metrics
   - Data quality

## Contributing

1. Fork the repository
2. Create your feature branch:
```bash
git checkout -b feature/my-feature
```
3. Commit your changes:
```bash
git commit -am 'Add new feature'
```
4. Push to the branch:
```bash
git push origin feature/my-feature
```
5. Submit a pull request

## Deployment

1. Configure production settings:
```bash
# Set production environment
export APP_ENV=production

# Update .env file
cp .env.prod .env
```

2. Deploy with Docker:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. Monitor deployment:
```bash
docker-compose logs -f
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Scrapy documentation
- Selenium documentation
- React documentation
- Docker documentation

## Support

For support, email support@example.com or create an issue in the repository.
``````markdown
# Jewelry Scraper - Project Documentation

## Directory Structure
```
jewelry_scraper/
│
├── backend/
│   ├── scraper/
│   │   ├── spiders/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Base spider class
│   │   │   ├── ebay_spider.py       # eBay-specific spider
│   │   │   └── amazon_spider.py     # Amazon-specific spider
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── proxy_manager.py     # Proxy rotation management
│   │   │   ├── rate_limiter.py      # Request rate limiting
│   │   │   └── image_processor.py   # Image handling utilities
│   │   │
│   │   └── orchestrator.py          # Main scraping coordinator
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── manager.py               # Database operations
│   │   └── models.py                # SQLAlchemy models
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py                   # Flask API endpoints
│   │
│   └── config/
│       ├── __init__.py
│       └── settings.py              # Configuration settings
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── DataDashboard.js
│   │   │   ├── DataTable.js
│   │   │   ├── EnhancedSearch.js
│   │   │   ├── ProductCard.js
│   │   │   └── SystemMonitor.js
│   │   │
│   │   ├── services/
│   │   │   └── api.js              # API integration
│   │   │
│   │   ├── context/
│   │   │   └── AppContext.js       # Global state
│   │   │
│   │   ├── App.js
│   │   └── index.js
│   │
│   ├── package.json
│   └── README.md
│
├── data/
│   ├── images/                      # Stored product images
│   └── backups/                     # Database backups
│
├── logs/                            # Application logs
│
├── tests/
│   ├── backend/
│   │   ├── test_spiders.py
│   │   ├── test_database.py
│   │   └── test_api.py
│   │
│   └── frontend/
│       └── components/
│           └── test_components.js
│
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
├── docker-compose.yml              # Docker configuration
└── README.md                       # Project documentation
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

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### 2. Configuration
Copy `.env.example` to `.env` and configure:
```env
# API Configuration
FLASK_APP=api/app.py
FLASK_ENV=development
PORT=5000

# Database
DATABASE_URL=sqlite:///jewelry_scraper.db

# Scraping Settings
MAX_CONCURRENT_REQUESTS=8
DOWNLOAD_DELAY=2
MAX_RETRIES=3

# Storage
IMAGE_STORAGE_PATH=data/images
BACKUP_PATH=data/backups

# Proxy Configuration (Optional)
PROXY_LIST_PATH=config/proxies.txt
```

### 3. Running the Application

#### Backend:
```bash
# Start Flask API
python -m flask run

# Or with development server
python api/app.py
```

#### Frontend:
```bash
cd frontend
npm start
```

## Usage Guide

### 1. Scraping Products

The application supports scraping from:
- eBay (jewelry category)
- Amazon (jewelry category)

#### Search Parameters:
- Query: Search term for jewelry items
- Platform: eBay or Amazon
- Max Items: Number of items to scrape
- Filters:
  - Price Range
  - Category
  - Condition
  - Sort Order

### 2. Features

#### Data Collection:
- Product details (title, price, description)
- Image downloading and optimization
- Seller information
- Product specifications

#### Monitoring:
- Real-time scraping progress
- System resource usage
- Error tracking
- Performance metrics

#### Data Management:
- Product browsing
- Filtering and sorting
- Export capabilities
- Image management

### 3. API Endpoints

```python
# Scraping Endpoints
POST /scrape                # Start scraping job
GET /scrape/status/<id>     # Check job status
POST /scrape/cancel/<id>    # Cancel job

# Product Endpoints
GET /products               # Get products with filters
DELETE /products            # Delete products
GET /products/export        # Export products

# System Endpoints
GET /system/status          # Get system metrics
GET /system/report          # Get performance report
```

### 4. Error Handling

The system includes:
- Automatic retry mechanism
- Proxy rotation
- Rate limiting
- Error logging
- Job recovery

### 5. Maintenance

Regular maintenance tasks:
```bash
# Database backup
python scripts/backup_db.py

# Clean old images
python scripts/cleanup_images.py

# Check system health
python scripts/health_check.py
```

### 6. Monitoring

Access monitoring dashboard at:
```
http://localhost:3000/dashboard
```

Features:
- Active jobs
- Success rates
- Resource usage
- Error rates

## Best Practices

1. Scraping:
   - Use appropriate delays between requests
   - Implement proxy rotation for large jobs
   - Monitor rate limiting
   - Validate scraped data

2. Data Storage:
   - Regular database backups
   - Clean up unused images
   - Monitor storage usage
   - Validate data integrity

3. Performance:
   - Limit concurrent requests
   - Optimize image storage
   - Use caching when appropriate
   - Monitor system resources

## Troubleshooting

Common issues and solutions:
1. Blocked Requests
   - Rotate proxies
   - Increase delays
   - Check user agents

2. Image Download Failures
   - Verify URLs
   - Check storage permissions
   - Monitor bandwidth usage

3. Database Issues
   - Check connections
   - Verify permissions
   - Monitor disk space

4. Memory Usage
   - Adjust batch sizes
   - Monitor resource usage
   - Clean up temporary files

## Contributing

Follow these guidelines:
1. Fork repository
2. Create feature branch
3. Write tests
4. Submit pull request

## License

MIT License - See LICENSE file for details
```

Would you like me to:
1. Add more technical details
2. Expand troubleshooting
3. Add deployment guides
4. Create additional documentation

The documentation focuses on practical usage while maintaining technical accuracy.
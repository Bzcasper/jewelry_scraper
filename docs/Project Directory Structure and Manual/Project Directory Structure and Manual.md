```markdown
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
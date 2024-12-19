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

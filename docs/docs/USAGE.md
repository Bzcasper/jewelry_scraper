
Usage Guide
This guide provides detailed instructions on how to use the Jewelry Scraper application effectively.

1. Scraping Products
Initiate a Scraping Job
Access the Frontend: Open your browser and navigate to http://localhost:3000.

Input Search Parameters:

Search Query: Enter the keyword for the jewelry items you want to scrape (e.g., "gold ring").
Platform Selection: Choose between eBay or Amazon.
Maximum Items: Specify the number of items to scrape.
Apply Filters (Optional):

Price Range: Set minimum and maximum price limits.
Category: Select specific jewelry categories like Rings, Necklaces, etc.
Condition: Choose between New, Used, or Both.
Sort Order: Sort results by price, relevance, or date.
Start Scraping: Click the "Search" button to initiate the scraping process.

Monitoring Scraping Progress
Real-time Updates: Monitor the progress through the DataDashboard component.
Logs: Check the logs directory (backend/logs/) for detailed logs.
2. Viewing Scraped Data
Through Frontend
DataTable: View all scraped products in a tabular format with sorting and filtering options.
DataDashboard: Visualize data through charts and statistics for better insights.
Through API
Retrieve All Products:

bash
GET http://localhost:5000/products
Filtered Retrieval: Add query parameters to filter results based on category, price, platform, etc.

Through Database
SQLite Database: Access the products.db SQLite database using any SQLite viewer for direct database interactions.
3. Managing Data
Exporting Data
Export Formats: CSV, JSON, Excel.
Procedure: Navigate to the export section in the frontend and choose your preferred format.
Triggering Database Backup
Manual Backup:

bash
Copy code
GET http://localhost:5000/backup
Backups are stored in the db_backups directory with timestamped filenames.

Automated Backups: Scheduled backups can be set up using cron jobs or other scheduling tools.

4. API Endpoints
Scraping Endpoints
Start Scraping Job:

bash
POST /scrape
Payload:

json
{
  "query": "gold necklace",
  "platform": "amazon",
  "max_items": 100
}
Check Job Status:

bash
GET /scrape/status/{job_id}
Cancel Scraping Job:

bash
POST /scrape/cancel/{job_id}
Product Endpoints
Get Products:

bash
GET /products
Query Parameters:

platform
category
price_min
price_max
condition
Delete Products:

bash
DELETE /products
Export Products:

bash
Copy code
GET /products/export
Parameters: format (csv, json, excel)

System Endpoints
Get System Metrics:

bash
Copy code
GET /system/status
Get Performance Report:

bash
Copy code
GET /system/report
5. Monitoring
Access the monitoring dashboard at http://localhost:3001.

Dashboard Features
Active Jobs: View currently running scraping jobs.
Success Rates: Monitor the success rate of scraping tasks.
Resource Usage: Track CPU, memory, and network usage.
Error Rates: View the frequency and types of errors encountered.
Alerting
Set up alerts for critical issues such as high error rates, slow response times, or resource constraints. Configure alerting rules in the monitoring tools (Prometheus/Grafana).

6. Maintenance
Regular Tasks
Database Backup:

bash
Copy code
python scripts/backup_db.py
Clean Up Old Images:

bash
Copy code
python scripts/cleanup_images.py
Health Check:

bash
Copy code
python scripts/health_check.py
Data Cleanup
Implement periodic data cleanup routines to remove duplicate or outdated entries and ensure data integrity.

7. Advanced Usage
Custom Scraping Parameters
Modify scraping parameters such as concurrency, delays, and retry attempts by editing the configuration files (config/scraping.py).

Proxy Management
Configure and manage proxies to enhance scraping resilience. Refer to Configuration for detailed proxy setup.

Extending the Application
Adding Support for More Platforms: Extend the scraper to include additional e-commerce platforms.
Implementing Machine Learning: Integrate ML models for category classification or price prediction.
For more advanced configurations and customization, refer to the Advanced Features documentation. 

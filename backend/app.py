import os
import uuid
import logging
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Optional
from dataclasses import dataclass
from scraper.controller import ScraperController
from scraper.monitor import ScraperMonitor
from database.manager import DatabaseManager
from utils.validators import validate_scraping_request
from utils.error_handlers import handle_error

# Set up Flask app
app = Flask(__name__)
CORS(app)

# Logging Configuration
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize core services
scraper_controller = ScraperController(max_workers=3)
scraper_monitor = ScraperMonitor()
db_manager = DatabaseManager()

@dataclass
class JobResponse:
    """Standardized job response structure."""
    success: bool
    job_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict] = None

def create_job_response(success: bool, **kwargs) -> Dict:
    """Create a standardized API response."""
    return JobResponse(success=success, **kwargs).__dict__

@app.route('/scrape', methods=['POST'])
def scrape():
    """Start a new scraping job."""
    try:
        data = request.json
        validation_error = validate_scraping_request(data)
        if validation_error:
            return jsonify(create_job_response(success=False, error=validation_error)), 400

        job_id = str(uuid.uuid4())
        job_params = {
            'query': data['query'],
            'platform': data.get('platform', 'ebay'),
            'max_items': int(data.get('max_items', 50)),
            'filters': data.get('filters', {}),
            'scraping_config': {
                'use_proxies': data.get('use_proxies', True),
                'retry_attempts': data.get('retry_attempts', 3),
                'download_images': data.get('download_images', True),
                'timeout': data.get('timeout', 30)
            }
        }
        scraper_controller.start_job(job_id, job_params)
        scraper_monitor.track_job_start(job_id, job_params)
        return jsonify(create_job_response(success=True, job_id=job_id, message="Scraping job started successfully"))
    except Exception as e:
        logger.error(f"Error starting scrape: {e}", exc_info=True)
        return handle_error(e)

@app.route('/scrape/status/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    """Get detailed status of a scraping job."""
    try:
        status = scraper_controller.get_job_status(job_id)
        if not status:
            return jsonify(create_job_response(success=False, error="Job not found")), 404

        metrics = scraper_monitor.get_job_metrics(job_id)
        return jsonify(create_job_response(success=True, data={
            'status': status,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }))
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        return handle_error(e)

@app.route('/scrape/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id: str):
    """Cancel an active scraping job."""
    try:
        success = scraper_controller.cancel_job(job_id)
        if success:
            scraper_monitor.track_job_cancellation(job_id)
            return jsonify(create_job_response(success=True, message="Job cancelled successfully"))
        return jsonify(create_job_response(success=False, error="Job not found or already completed")), 404
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        return handle_error(e)

@app.route('/products', methods=['GET'])
def get_products():
    """Get scraped products with filtering and pagination."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        sort_by = request.args.get('sort_by', 'date_scraped')
        sort_order = request.args.get('sort_order', 'desc')
        filters = request.args.get('filters', {})

        products, total = db_manager.get_products(
            filters=filters, page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)

        return jsonify(create_job_response(success=True, data={
            'products': products,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }))
    except Exception as e:
        logger.error(f"Error fetching products: {e}", exc_info=True)
        return handle_error(e)

@app.route('/system/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system status and performance metrics."""
    try:
        metrics = scraper_monitor.get_metrics()
        db_stats = db_manager.get_stats()
        jobs_summary = scraper_controller.get_jobs_summary()

        return jsonify(create_job_response(success=True, data={
            'metrics': metrics.__dict__,
            'database': db_stats,
            'jobs': jobs_summary,
            'timestamp': datetime.now().isoformat()
        }))
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        return handle_error(e)

def background_task():
    """Run maintenance tasks periodically."""
    while True:
        try:
            scraper_controller.cleanup_jobs()
            db_manager.optimize()
            scraper_monitor.update_stats()
        except Exception as e:
            logger.error(f"Background task error: {e}", exc_info=True)
        time.sleep(3600)  # Run every hour

# Start background tasks in a separate thread
threading.Thread(target=background_task, daemon=True).start()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )

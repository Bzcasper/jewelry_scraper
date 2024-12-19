from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from scraper.ebay_spider import run_ebay_spider
from scraper.amazon_spider import run_amazon_spider
from database.db import (
    initialize_db, add_product, fetch_all_products,
    fetch_products_by_filters, update_product, delete_products,
    get_product_stats, add_scraping_job, update_scraping_job
)
from database.backup import backup_database, restore_database
from logger import log_error, log_critical_error
import logging
from datetime import datetime
import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Enhanced Flask configuration
app = Flask(__name__)
CORS(app)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure caching
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Configure background task executor
executor = ThreadPoolExecutor(max_workers=3)

# Initialize the database
initialize_db()

@dataclass
class ScrapingJob:
    id: str
    status: str
    progress: int
    results: List[Dict]
    error: Optional[str] = None

# In-memory job tracking
active_jobs: Dict[str, ScrapingJob] = {}

def generate_job_id(query: str, platform: str) -> str:
    """Generate a unique job ID based on query parameters"""
    return hashlib.md5(f"{query}:{platform}:{datetime.now()}".encode()).hexdigest()

def background_scrape(job_id: str, query: str, platform: str, max_items: int, filters: Dict = None):
    """Background scraping task with progress tracking"""
    try:
        # Update job status
        active_jobs[job_id].status = "running"
        add_scraping_job(job_id, "running", query, platform)

        # Run the appropriate spider
        if platform == "ebay":
            results = run_ebay_spider(query, max_items, filters)
        elif platform == "amazon":
            results = run_amazon_spider(query, max_items, filters)
        else:
            raise ValueError("Unsupported platform")

        # Store results in the database
        for i, product in enumerate(results):
            add_product(product)
            # Update progress
            progress = int((i + 1) / len(results) * 100)
            active_jobs[job_id].progress = progress
            update_scraping_job(job_id, progress=progress)

        # Update job completion
        active_jobs[job_id].status = "completed"
        active_jobs[job_id].results = results
        update_scraping_job(job_id, status="completed", results=results)

    except Exception as e:
        error_msg = str(e)
        log_error(f"Error during scraping job {job_id}: {error_msg}")
        active_jobs[job_id].status = "failed"
        active_jobs[job_id].error = error_msg
        update_scraping_job(job_id, status="failed", error=error_msg)

@app.route('/scrape', methods=['POST'])
@limiter.limit("10 per minute")
async def scrape():
    """
    Asynchronously scrapes eBay or Amazon based on the user's query.
    Returns a job ID for tracking progress.
    """
    try:
        data = request.json
        query = data.get("query", "").strip()
        platform = data.get("platform", "ebay")
        max_items = data.get("max_items", 50)
        filters = data.get("filters", {})

        # Validate input
        if not query:
            return jsonify({"error": "Query is required"}), 400
        if not isinstance(max_items, int) or max_items < 1:
            return jsonify({"error": "Invalid max_items value"}), 400
        if platform not in ["ebay", "amazon"]:
            return jsonify({"error": "Unsupported platform"}), 400

        # Generate job ID and create job
        job_id = generate_job_id(query, platform)
        active_jobs[job_id] = ScrapingJob(
            id=job_id,
            status="pending",
            progress=0,
            results=[]
        )

        # Start background task
        executor.submit(
            background_scrape,
            job_id,
            query,
            platform,
            max_items,
            filters
        )

        return jsonify({
            "message": "Scraping job started",
            "job_id": job_id
        })

    except Exception as e:
        log_error(f"Error initiating scraping job: {e}")
        return jsonify({"error": "Failed to start scraping job"}), 500

@app.route('/scrape/status/<job_id>', methods=['GET'])
@cache.memoize(timeout=10)
def get_job_status(job_id):
    """Get the status of a scraping job"""
    job = active_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "results": job.results if job.status == "completed" else None
    })

@app.route('/products', methods=['GET'])
@cache.cached(timeout=60)
def get_products():
    """
    Fetch products from the database with filtering and pagination.
    """
    try:
        # Get filter parameters
        filters = {
            'platform': request.args.get('platform'),
            'category': request.args.get('category'),
            'price_min': request.args.get('price_min', type=float),
            'price_max': request.args.get('price_max', type=float),
            'date_min': request.args.get('date_min'),
            'date_max': request.args.get('date_max')
        }

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Get sorting parameters
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')

        # Fetch filtered products
        products, total_count = fetch_products_by_filters(
            filters,
            page,
            per_page,
            sort_by,
            sort_order
        )

        return jsonify({
            "products": products,
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page
        })

    except Exception as e:
        log_error(f"Error fetching products: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500

@app.route('/products/stats', methods=['GET'])
@cache.cached(timeout=300)
def get_stats():
    """
    Get statistical information about scraped products.
    """
    try:
        stats = get_product_stats()
        return jsonify(stats)
    except Exception as e:
        log_error(f"Error fetching product stats: {e}")
        return jsonify({"error": "Failed to fetch product statistics"}), 500

@app.route('/products/<int:product_id>', methods=['PUT', 'DELETE'])
def manage_product(product_id):
    """
    Update or delete a specific product.
    """
    try:
        if request.method == 'PUT':
            data = request.json
            update_product(product_id, data)
            cache.delete_memoized(get_products)
            return jsonify({"message": "Product updated successfully"})
        else:  # DELETE
            delete_products([product_id])
            cache.delete_memoized(get_products)
            return jsonify({"message": "Product deleted successfully"})
    except Exception as e:
        log_error(f"Error managing product {product_id}: {e}")
        return jsonify({"error": f"Failed to {request.method.lower()} product"}), 500

@app.route('/backup', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def manage_backup():
    """
    Manage database backups - create or restore.
    """
    try:
        if request.method == 'GET':
            backup_file = backup_database()
            return jsonify({
                "message": "Database backup completed",
                "backup_file": backup_file
            })
        else:  # POST for restore
            backup_file = request.json.get('backup_file')
            if not backup_file:
                return jsonify({"error": "Backup file path is required"}), 400
            restore_database(backup_file)
            cache.delete_memoized(get_products)
            return jsonify({"message": "Database restored successfully"})
    except Exception as e:
        log_error(f"Error managing backup: {e}")
        return jsonify({"error": "Backup operation failed"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    return jsonify({"error": "Rate limit exceeded"}), 429

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
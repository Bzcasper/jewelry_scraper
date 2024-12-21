# File: /backend/api/app.py

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import asyncio
import logging
from datetime import datetime
import uuid

from database.manager import DatabaseManager
from scraper.spiders.ebay_spider import EbayJewelrySpider
from scraper.spiders.amazon_spider import AmazonJewelrySpider
from utils.image_processor import ImageProcessor

# Initialize FastAPI app
app = FastAPI(title="Jewelry Scraper API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager()
image_processor = ImageProcessor()
active_jobs = {}

class ScrapeRequest(BaseModel):
    """Scraping request model"""
    query: str
    platform: str = "ebay"
    max_items: int = Field(default=50, ge=1, le=200)
    filters: Dict = {}

class JobStatus(BaseModel):
    """Job status model"""
    id: str
    status: str
    progress: float
    items_scraped: int
    error: Optional[str] = None
    start_time: datetime

async def scrape_products(job_id: str, request: ScrapeRequest):
    """Background task for scraping products"""
    try:
        # Select spider based on platform
        spider_class = EbayJewelrySpider if request.platform == "ebay" else AmazonJewelrySpider
        
        async with spider_class() as spider:
            # Update job status
            active_jobs[job_id].status = "running"
            
            # Start scraping
            products = await spider.scrape_query(
                query=request.query,
                max_items=request.max_items
            )
            
            # Process and store products
            for i, product in enumerate(products):
                # Process images
                if product.get('images'):
                    processed_images = await image_processor.process_images(
                        product['images'],
                        str(uuid.uuid4())
                    )
                    product['images'] = processed_images

                # Store in database
                await db.add_product(product)
                
                # Update progress
                active_jobs[job_id].progress = (i + 1) / len(products) * 100
                active_jobs[job_id].items_scraped = i + 1

            # Mark job as completed
            active_jobs[job_id].status = "completed"
            
    except Exception as e:
        logging.error(f"Scraping error in job {job_id}: {str(e)}")
        active_jobs[job_id].status = "failed"
        active_jobs[job_id].error = str(e)

@app.post("/scrape")
async def start_scraping(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Start a new scraping job"""
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    active_jobs[job_id] = JobStatus(
        id=job_id,
        status="pending",
        progress=0.0,
        items_scraped=0,
        start_time=datetime.now()
    )
    
    # Start scraping task in background
    background_tasks.add_task(scrape_products, job_id, request)
    
    return {"job_id": job_id}

@app.get("/scrape/status/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a scraping job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return active_jobs[job_id]

@app.get("/products")
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    platform: Optional[str] = None,
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "date_scraped",
    sort_desc: bool = True
):
    """Get scraped products with filtering and pagination"""
    filters = {
        "platform": platform,
        "category": category,
        "price_min": price_min,
        "price_max": price_max,
        "search": search
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    products, total = await db.get_products(
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_desc=sort_desc
    )
    
    return {
        "products": products,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@app.delete("/products")
async def delete_products(ids: List[int]):
    """Delete products by IDs"""
    success = await db.delete_products(ids)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete products")
    return {"success": True}

@app.get("/system/status")
async def get_system_status():
    """Get system status and statistics"""
    stats = await db.get_stats()
    active_job_stats = {
        "total": len(active_jobs),
        "running": sum(1 for job in active_jobs.values() if job.status == "running"),
        "completed": sum(1 for job in active_jobs.values() if job.status == "completed"),
        "failed": sum(1 for job in active_jobs.values() if job.status == "failed")
    }
    
    return {
        "database": stats,
        "jobs": active_job_stats,
        "last_updated": datetime.now().isoformat()
    }

# Cleanup job for completed/failed jobs
@app.on_event("startup")
@app.on_event("shutdown")
async def cleanup_jobs():
    """Clean up old jobs and resources"""
    # Remove completed/failed jobs older than 1 hour
    current_time = datetime.now()
    jobs_to_remove = [
        job_id for job_id, job in active_jobs.items()
        if job.status in ("completed", "failed") and 
        (current_time - job.start_time).total_seconds() > 3600
    ]
    
    for job_id in jobs_to_remove:
        del active_jobs[job_id]
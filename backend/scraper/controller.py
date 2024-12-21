# File: /backend/scraper/controller.py

from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .spiders.ebay_spider import EbayJewelrySpider
from .spiders.amazon_spider import AmazonJewelrySpider
from .middleware import ScraperMiddleware
from database.manager import DatabaseManager
from utils.image_processor import ImageProcessor

@dataclass
class ScrapingJob:
    """Scraping job status and configuration"""
    id: str
    platform: str
    query: str
    max_items: int
    filters: Dict
    start_time: datetime
    status: str = "pending"
    progress: float = 0.0
    items_scraped: int = 0
    errors: List[str] = None

class ScraperController:
    """Manage scraping operations and job coordination"""
    
    def __init__(self, max_workers: int = 3):
        self.middleware = ScraperMiddleware()
        self.db = DatabaseManager()
        self.image_processor = ImageProcessor()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_jobs: Dict[str, ScrapingJob] = {}
        self.logger = logging.getLogger(__name__)

    async def start_job(self, job_id: str, config: Dict) -> Optional[str]:
        """Start new scraping job"""
        try:
            job = ScrapingJob(
                id=job_id,
                platform=config['platform'],
                query=config['query'],
                max_items=config.get('max_items', 50),
                filters=config.get('filters', {}),
                start_time=datetime.now(),
                errors=[]
            )
            
            self.active_jobs[job_id] = job
            
            # Start job in background
            asyncio.create_task(self._run_job(job))
            
            return job_id

        except Exception as e:
            self.logger.error(f"Failed to start job: {e}")
            return None

    async def _run_job(self, job: ScrapingJob):
        """Execute scraping job"""
        try:
            job.status = "running"
            
            # Select appropriate spider
            spider_class = EbayJewelrySpider if job.platform == "ebay" else AmazonJewelrySpider
            
            async with spider_class() as spider:
                results = await spider.scrape_query(
                    query=job.query,
                    max_items=job.max_items,
                    filters=job.filters
                )
                
                # Process results
                for i, product in enumerate(results):
                    try:
                        # Process images
                        if product.get('images'):
                            processed_images = await self.image_processor.process_images(
                                product['images'],
                                str(job.id)
                            )
                            product['images'] = processed_images
                        
                        # Store in database
                        await self.db.add_product(product)
                        
                        job.items_scraped += 1
                        job.progress = (i + 1) / len(results) * 100
                        
                    except Exception as e:
                        job.errors.append(str(e))
                        self.logger.error(f"Error processing product: {e}")
                
            job.status = "completed"
            
        except Exception as e:
            job.status = "failed"
            job.errors.append(str(e))
            self.logger.error(f"Job failed: {e}")

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current job status"""
        if job := self.active_jobs.get(job_id):
            return {
                'status': job.status,
                'progress': job.progress,
                'items_scraped': job.items_scraped,
                'errors': job.errors,
                'duration': (datetime.now() - job.start_time).total_seconds()
            }
        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel running job"""
        if job := self.active_jobs.get(job_id):
            if job.status == "running":
                job.status = "cancelled"
                return True
        return False

    async def cleanup_jobs(self):
        """Clean up completed/failed jobs"""
        to_remove = []
        for job_id, job in self.active_jobs.items():
            if job.status in ["completed", "failed", "cancelled"]:
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.active_jobs[job_id]
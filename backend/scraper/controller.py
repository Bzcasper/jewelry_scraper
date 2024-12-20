from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging
from typing import Dict, List
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from .spiders.ebay_spider import EbayJewelrySpider
from .spiders.amazon_spider import AmazonJewelrySpider

@dataclass
class ScrapingJob:
    id: str
    query: str
    platform: str
    max_items: int
    filters: Dict
    start_time: datetime
    status: str = 'pending'
    progress: float = 0
    results: List = None
    error: str = None

class ScraperController:
    """Manages scraping operations and job coordination"""
    
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_jobs: Dict[str, ScrapingJob] = {}
        self.session = aiohttp.ClientSession()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )

    async def start_job(self, job_id: str, params: Dict) -> ScrapingJob:
        """Start a new scraping job"""
        job = ScrapingJob(
            id=job_id,
            query=params['query'],
            platform=params['platform'],
            max_items=params.get('max_items', 50),
            filters=params.get('filters', {}),
            start_time=datetime.now()
        )
        
        self.active_jobs[job_id] = job
        
        # Start job in thread pool
        self.executor.submit(self._run_job, job)
        return job

    def _run_job(self, job: ScrapingJob):
        """Execute scraping job"""
        try:
            # Select appropriate spider
            spider_class = {
                'ebay': EbayJewelrySpider,
                'amazon': AmazonJewelrySpider
            }.get(job.platform)
            
            if not spider_class:
                raise ValueError(f"Unsupported platform: {job.platform}")

            # Configure spider settings
            settings = {
                'DOWNLOAD_DELAY': 2,
                'CONCURRENT_REQUESTS': 8,
                'RETRY_TIMES': 3,
                'LOG_LEVEL': 'INFO',
                'ITEM_PIPELINES': {
                    'scraper.pipelines.JewelryPipeline': 300,
                    'scraper.pipelines.ImagePipeline': 200
                }
            }

            # Initialize and run spider
            spider = spider_class(
                query=job.query,
                max_items=job.max_items,
                filters=job.filters
            )
            
            # Monitor progress
            def progress_callback(stats):
                items_scraped = stats.get('items_scraped', 0)
                job.progress = min(100, (items_scraped / job.max_items) * 100)
                job.status = 'running'

            # Run spider with progress monitoring
            results = spider.run(settings, progress_callback)
            
            # Update job with results
            job.results = results
            job.status = 'completed'
            logging.info(f"Job {job.id} completed with {len(results)} items")

        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            logging.error(f"Job {job.id} failed: {e}")

    async def get_job_status(self, job_id: str) -> Dict:
        """Get current status of a job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return {'error': 'Job not found'}
            
        return {
            'status': job.status,
            'progress': job.progress,
            'results': job.results if job.status == 'completed' else None,
            'error': job.error,
            'duration': (datetime.now() - job.start_time).total_seconds()
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel an active job"""
        job = self.active_jobs.get(job_id)
        if job and job.status == 'running':
            job.status = 'cancelled'
            return True
        return False

    async def cleanup_jobs(self):
        """Clean up completed jobs older than 1 hour"""
        current_time = datetime.now()
        to_remove = []
        
        for job_id, job in self.active_jobs.items():
            if job.status in ['completed', 'failed', 'cancelled']:
                duration = (current_time - job.start_time).total_seconds()
                if duration > 3600:  # 1 hour
                    to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.active_jobs[job_id]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        self.executor.shutdown()
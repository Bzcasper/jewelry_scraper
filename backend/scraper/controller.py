from concurrent.futures import ThreadPoolExecutor
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
import hashlib
from .spiders.ebay_spider import EbayJewelrySpider
from .spiders.amazon_spider import AmazonJewelrySpider
from database.manager import DatabaseManager
from .monitor import ScraperMonitor
from utils.proxy_manager import ProxyManager
from utils.image_processor import ImageProcessor

@dataclass
class ScrapingJob:
    """Represents a scraping job with all necessary metadata"""
    id: str
    query: str
    platform: str
    max_items: int
    filters: Dict
    start_time: datetime
    status: str = 'pending'
    progress: float = 0
    items_scraped: int = 0
    error_count: int = 0
    results: List = None
    error: Optional[str] = None
    last_updated: datetime = None
    proxy_used: Optional[str] = None
    bandwidth_used: float = 0
    retry_count: int = 0

class ScraperController:
    """Manages scraping operations and job coordination"""
    
    def __init__(self, 
                 max_workers: int = 3,
                 max_retries: int = 3,
                 job_timeout: int = 3600):
        # Core components
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_jobs: Dict[str, ScrapingJob] = {}
        self.db = DatabaseManager()
        self.monitor = ScraperMonitor()
        self.proxy_manager = ProxyManager()
        self.image_processor = ImageProcessor()
        
        # Configuration
        self.max_retries = max_retries
        self.job_timeout = job_timeout
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    async def start_job(self, job_id: str, params: Dict) -> ScrapingJob:
        """Initialize and start a new scraping job"""
        try:
            # Create job instance
            job = ScrapingJob(
                id=job_id,
                query=params['query'],
                platform=params['platform'],
                max_items=params.get('max_items', 50),
                filters=params.get('filters', {}),
                start_time=datetime.now()
            )
            
            # Store job
            self.active_jobs[job_id] = job
            
            # Start job execution
            self.executor.submit(self._execute_job, job)
            
            # Log job start
            self.logger.info(f"Started job {job_id} for query: {params['query']}")
            
            return job

        except Exception as e:
            self.logger.error(f"Error starting job {job_id}: {str(e)}")
            raise

    async def _execute_job(self, job: ScrapingJob):
        """Execute scraping job with error handling and retries"""
        try:
            # Select appropriate spider
            spider_class = self._get_spider_class(job.platform)
            
            # Configure spider settings
            settings = self._build_spider_settings(job)
            
            # Initialize spider
            spider = spider_class(
                query=job.query,
                max_items=job.max_items,
                filters=job.filters,
                settings=settings
            )
            
            # Track progress
            def progress_callback(stats):
                self._update_job_progress(job, stats)
            
            spider.set_progress_callback(progress_callback)
            
            # Run spider with proxy rotation
            while job.retry_count < self.max_retries:
                try:
                    # Get proxy
                    proxy = self.proxy_manager.get_proxy()
                    job.proxy_used = proxy.address
                    
                    # Run spider
                    results = await spider.run_async(proxy=proxy)
                    
                    # Process results
                    processed_results = await self._process_results(results, job)
                    
                    # Store results
                    await self._store_results(processed_results, job)
                    
                    # Update job status
                    job.status = 'completed'
                    job.results = processed_results
                    job.last_updated = datetime.now()
                    
                    # Log success
                    self.logger.info(f"Job {job.id} completed successfully")
                    
                    return
                    
                except Exception as e:
                    job.error_count += 1
                    job.retry_count += 1
                    job.error = str(e)
                    
                    self.logger.warning(
                        f"Attempt {job.retry_count} failed for job {job.id}: {str(e)}"
                    )
                    
                    if job.retry_count >= self.max_retries:
                        raise
                    
                    # Wait before retry
                    await asyncio.sleep(job.retry_count * 5)
            
        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            self.logger.error(f"Job {job.id} failed: {str(e)}")
            
        finally:
            # Cleanup
            self._cleanup_job(job)

    def _get_spider_class(self, platform: str):
        """Get appropriate spider class based on platform"""
        spiders = {
            'ebay': EbayJewelrySpider,
            'amazon': AmazonJewelrySpider
        }
        if platform not in spiders:
            raise ValueError(f"Unsupported platform: {platform}")
        return spiders[platform]

    def _build_spider_settings(self, job: ScrapingJob) -> Dict:
        """Build spider settings based on job configuration"""
        return {
            'CONCURRENT_REQUESTS': 8,
            'DOWNLOAD_DELAY': 2,
            'COOKIES_ENABLED': True,
            'RETRY_TIMES': 3,
            'TIMEOUT': 30,
            'USER_AGENT': self._get_user_agent(job),
            'ROBOTSTXT_OBEY': True,
            'DOWNLOAD_HANDLERS': {
                'image/*': 'scrapy.pipelines.files.FilesPipeline'
            },
            'ITEM_PIPELINES': {
                'scraper.pipelines.ValidationPipeline': 100,
                'scraper.pipelines.ImagePipeline': 200,
                'scraper.pipelines.DatabasePipeline': 300
            }
        }

    async def _process_results(self, results: List[Dict], job: ScrapingJob) -> List[Dict]:
        """Process and validate scraping results"""
        processed_results = []
        
        for item in results:
            try:
                # Validate item
                if not self._validate_item(item):
                    continue
                
                # Process images
                if item.get('image_urls'):
                    item['images'] = await self.image_processor.process_images(
                        item['image_urls'],
                        job.id
                    )
                
                # Clean and normalize data
                cleaned_item = self._clean_item(item)
                
                processed_results.append(cleaned_item)
                job.items_scraped += 1
                
            except Exception as e:
                job.error_count += 1
                self.logger.error(f"Error processing item: {str(e)}")
                
        return processed_results

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current status of a job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return None
            
        return {
            'status': job.status,
            'progress': job.progress,
            'items_scraped': job.items_scraped,
            'error_count': job.error_count,
            'error': job.error,
            'duration': (datetime.now() - job.start_time).total_seconds(),
            'bandwidth_used': job.bandwidth_used,
            'results': job.results if job.status == 'completed' else None
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel an active job"""
        job = self.active_jobs.get(job_id)
        if job and job.status == 'running':
            job.status = 'cancelled'
            self._cleanup_job(job)
            return True
        return False

    async def cleanup_jobs(self):
        """Clean up completed and old jobs"""
        current_time = datetime.now()
        to_remove = []
        
        for job_id, job in self.active_jobs.items():
            # Remove completed jobs after 1 hour
            if job.status in ['completed', 'failed', 'cancelled']:
                if (current_time - job.start_time).total_seconds() > 3600:
                    to_remove.append(job_id)
                    
            # Cancel stuck jobs
            elif (current_time - job.start_time).total_seconds() > self.job_timeout:
                job.status = 'failed'
                job.error = 'Job timeout exceeded'
                to_remove.append(job_id)
        
        for job_id in to_remove:
            self._cleanup_job(self.active_jobs[job_id])
            del self.active_jobs[job_id]

    def get_jobs_summary(self) -> Dict:
        """Get summary of all jobs"""
        return {
            'total_jobs': len(self.active_jobs),
            'running': len([j for j in self.active_jobs.values() if j.status == 'running']),
            'completed': len([j for j in self.active_jobs.values() if j.status == 'completed']),
            'failed': len([j for j in self.active_jobs.values() if j.status == 'failed'])
        }

    def _cleanup_job(self, job: ScrapingJob):
        """Perform job cleanup"""
        try:
            # Release proxy
            if job.proxy_used:
                self.proxy_manager.release_proxy(job.proxy_used)
            
            # Update monitoring stats
            self.monitor.track_job_completion(job)
            
            # Log completion
            self.logger.info(
                f"Job {job.id} cleanup completed. "
                f"Status: {job.status}, Items: {job.items_scraped}"
            )
            
        except Exception as e:
            self.logger.error(f"Error during job cleanup: {str(e)}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=True)
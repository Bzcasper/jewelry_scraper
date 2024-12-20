from concurrent.futures import ThreadPoolExecutor
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
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
    status: str = "pending"
    progress: float = 0.0
    items_scraped: int = 0
    error_count: int = 0
    results: Optional[List[Dict]] = None
    error: Optional[str] = None
    last_updated: Optional[datetime] = None
    proxy_used: Optional[str] = None
    bandwidth_used: float = 0.0
    retry_count: int = 0


class ScraperController:
    """Manages scraping operations and job coordination"""

    def __init__(self, max_workers: int = 3, max_retries: int = 3, job_timeout: int = 3600):
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
            job = ScrapingJob(
                id=job_id,
                query=params['query'],
                platform=params['platform'],
                max_items=params.get('max_items', 50),
                filters=params.get('filters', {}),
                start_time=datetime.now(),
            )
            self.active_jobs[job_id] = job

            # Start the job asynchronously
            self.executor.submit(asyncio.run, self._execute_job(job))
            self.logger.info(f"Started job {job_id} for query: {params['query']}")
            return job
        except Exception as e:
            self.logger.error(f"Error starting job {job_id}: {str(e)}", exc_info=True)
            raise

    async def _execute_job(self, job: ScrapingJob):
        """Execute scraping job with retries and error handling"""
        try:
            spider_class = self._get_spider_class(job.platform)
            settings = self._build_spider_settings(job)
            spider = spider_class(query=job.query, max_items=job.max_items, filters=job.filters, settings=settings)

            for attempt in range(self.max_retries):
                try:
                    proxy = self.proxy_manager.get_proxy()
                    job.proxy_used = proxy.address

                    # Run the spider and process results
                    results = await spider.run_async(proxy=proxy)
                    processed_results = await self._process_results(results, job)

                    await self._store_results(processed_results, job)
                    job.status = "completed"
                    job.results = processed_results
                    job.last_updated = datetime.now()
                    self.logger.info(f"Job {job.id} completed successfully")
                    return
                except Exception as e:
                    job.retry_count += 1
                    self.logger.warning(f"Attempt {attempt + 1} for job {job.id} failed: {str(e)}", exc_info=True)
                    if attempt + 1 >= self.max_retries:
                        raise
                    await asyncio.sleep(5 * (attempt + 1))

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            self.logger.error(f"Job {job.id} failed: {str(e)}", exc_info=True)
        finally:
            self._cleanup_job(job)

    def _get_spider_class(self, platform: str):
        spiders = {"ebay": EbayJewelrySpider, "amazon": AmazonJewelrySpider}
        if platform not in spiders:
            raise ValueError(f"Unsupported platform: {platform}")
        return spiders[platform]

    def _build_spider_settings(self, job: ScrapingJob) -> Dict:
        return {
            "CONCURRENT_REQUESTS": 8,
            "DOWNLOAD_DELAY": 2,
            "COOKIES_ENABLED": True,
            "RETRY_TIMES": 3,
            "USER_AGENT": f"ScraperController/Job-{job.id}",
            "ROBOTSTXT_OBEY": True,
        }

    async def _process_results(self, results: List[Dict], job: ScrapingJob) -> List[Dict]:
        processed_results = []
        for item in results:
            try:
                # Process images if available
                if "image_urls" in item:
                    item["images"] = await self.image_processor.process_images(item["image_urls"], job.id)
                processed_results.append(item)
                job.items_scraped += 1
            except Exception as e:
                job.error_count += 1
                self.logger.error(f"Error processing result: {e}", exc_info=True)
        return processed_results

    async def _store_results(self, results: List[Dict], job: ScrapingJob):
        await self.db.store_items(results)

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        job = self.active_jobs.get(job_id)
        if not job:
            return None
        return {
            "status": job.status,
            "progress": job.progress,
            "items_scraped": job.items_scraped,
            "error_count": job.error_count,
            "error": job.error,
            "results": job.results if job.status == "completed" else None,
        }

    async def cancel_job(self, job_id: str) -> bool:
        job = self.active_jobs.get(job_id)
        if job and job.status == "running":
            job.status = "cancelled"
            self._cleanup_job(job)
            return True
        return False

    async def cleanup_jobs(self):
        to_remove = [job_id for job_id, job in self.active_jobs.items() if job.status in ["completed", "failed"]]
        for job_id in to_remove:
            self._cleanup_job(self.active_jobs[job_id])
            del self.active_jobs[job_id]

    def _cleanup_job(self, job: ScrapingJob):
        try:
            if job.proxy_used:
                self.proxy_manager.release_proxy(job.proxy_used)
            self.monitor.track_job_completion(job)
        except Exception as e:
            self.logger.error(f"Error during cleanup for job {job.id}: {str(e)}", exc_info=True)

# File: /backend/scraper/orchestrator.py

from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, field
from .spiders.base import JewelrySpiderBase
from .spiders.ebay_spider import EbayJewelrySpider
from .spiders.amazon_spider import AmazonJewelrySpider
from database.manager import DatabaseManager
from utils.image_processor import ImageProcessor
from utils.proxy_manager import ProxyManager
from .monitor import ScraperMonitor

@dataclass
class ScrapingTask:
    """Represents a single scraping task"""
    id: str
    platform: str
    query: str
    max_items: int
    filters: Dict
    start_time: datetime = field(default_factory=datetime.now)
    status: str = 'pending'
    items_scraped: int = 0
    errors: List[str] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)

class ScrapingOrchestrator:
    """Manages and coordinates scraping operations"""
    
    def __init__(self):
        # Core components
        self.db = DatabaseManager()
        self.image_processor = ImageProcessor()
        self.proxy_manager = ProxyManager()
        self.monitor = ScraperMonitor()
        self.logger = logging.getLogger(__name__)
        
        # Active tasks tracking
        self.active_tasks: Dict[str, ScrapingTask] = {}
        
        # Platform-specific configurations
        self.platform_configs = {
            'ebay': {
                'spider': EbayJewelrySpider,
                'rate_limit': 2.0,
                'max_retries': 3,
                'proxy_required': True
            },
            'amazon': {
                'spider': AmazonJewelrySpider,
                'rate_limit': 2.5,
                'max_retries': 3,
                'proxy_required': True
            }
        }

    async def start_scraping(self, task_id: str, params: Dict) -> ScrapingTask:
        """Start a new scraping task"""
        try:
            task = ScrapingTask(
                id=task_id,
                platform=params['platform'],
                query=params['query'],
                max_items=params.get('max_items', 50),
                filters=params.get('filters', {})
            )
            
            self.active_tasks[task_id] = task
            asyncio.create_task(self._execute_task(task))
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to start task {task_id}: {str(e)}")
            raise

    async def _execute_task(self, task: ScrapingTask):
        """Execute scraping task with error handling and retries"""
        proxy = None
        try:
            config = self.platform_configs.get(task.platform)
            if not config:
                raise ValueError(f"Unsupported platform: {task.platform}")

            # Get proxy if required
            if config['proxy_required']:
                proxy = await self.proxy_manager.get_proxy()

            # Initialize and run spider
            spider = config['spider'](
                query=task.query,
                max_items=task.max_items,
                filters=task.filters
            )
            
            spider.set_progress_callback(
                lambda stats: self._update_task_progress(task, stats)
            )
            
            results = await self._scrape_with_retries(
                spider=spider,
                proxy=proxy,
                max_retries=config['max_retries'],
                rate_limit=config['rate_limit']
            )
            
            # Process and store results
            task.results = await self._process_results(results, task)
            task.status = 'completed'
            
        except Exception as e:
            task.status = 'failed'
            task.errors.append(str(e))
            self.logger.error(f"Task {task.id} failed: {str(e)}")
            
        finally:
            if proxy:
                await self.proxy_manager.release_proxy(proxy)
            await self._cleanup_task(task)

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
            
        return {
            'status': task.status,
            'items_scraped': task.items_scraped,
            'errors': task.errors,
            'duration': (datetime.now() - task.start_time).total_seconds(),
            'results': task.results if task.status == 'completed' else None
        }

    async def cleanup(self):
        """Clean up resources and cancel active tasks"""
        try:
            for task in self.active_tasks.values():
                if task.status == 'running':
                    task.status = 'cancelled'
            
            await asyncio.gather(
                self.proxy_manager.cleanup(),
                self.image_processor.cleanup()
            )
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
from typing import Dict, List, Optional, Union
import asyncio
import logging
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from .spiders.base import JewelrySpiderBase
from .spiders.ebay_spider import EbayJewelrySpider
from .spiders.amazon_spider import AmazonJewelrySpider
from .database.manager import DatabaseManager
from .utils.image_processor import ImageProcessor
from .utils.proxy_manager import ProxyManager
from .monitor import ScraperMonitor

@dataclass
class ScrapingTask:
    """Represents a single scraping task"""
    id: str
    platform: str
    query: str
    max_items: int
    filters: Dict
    start_time: datetime
    status: str = 'pending'
    items_scraped: int = 0
    errors: List[str] = None
    results: List[Dict] = None

class ScrapingOrchestrator:
    """Manages and coordinates scraping operations"""
    
    def __init__(self):
        # Initialize components
        self.db = DatabaseManager()
        self.image_processor = ImageProcessor()
        self.proxy_manager = ProxyManager()
        self.monitor = ScraperMonitor()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Active tasks tracking
        self.active_tasks: Dict[str, ScrapingTask] = {}
        
        # Platform configurations
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
        """Initialize and start a scraping task"""
        try:
            # Create task
            task = ScrapingTask(
                id=task_id,
                platform=params['platform'],
                query=params['query'],
                max_items=params.get('max_items', 50),
                filters=params.get('filters', {}),
                start_time=datetime.now(),
                errors=[]
            )
            
            self.active_tasks[task_id] = task
            
            # Start scraping in background
            asyncio.create_task(self._execute_task(task))
            
            return task
            
        except Exception as e:
            self.logger.error(f"Failed to start task {task_id}: {str(e)}")
            raise

    async def _execute_task(self, task: ScrapingTask):
        """Execute scraping task with error handling"""
        try:
            # Get platform config
            config = self.platform_configs.get(task.platform)
            if not config:
                raise ValueError(f"Unsupported platform: {task.platform}")
            
            # Setup spider with proxy if required
            proxy = None
            if config['proxy_required']:
                proxy = await self.proxy_manager.get_proxy()
            
            # Initialize spider
            spider = config['spider'](
                query=task.query,
                max_items=task.max_items,
                filters=task.filters
            )
            
            # Set progress callback
            spider.set_progress_callback(
                lambda stats: self._update_task_progress(task, stats)
            )
            
            # Execute scraping
            results = await self._scrape_with_retries(
                spider=spider,
                proxy=proxy,
                max_retries=config['max_retries'],
                rate_limit=config['rate_limit']
            )
            
            # Process results
            processed_results = await self._process_results(results, task)
            
            # Update task status
            task.status = 'completed'
            task.results = processed_results
            
            # Log completion
            self.logger.info(
                f"Task {task.id} completed. "
                f"Items scraped: {task.items_scraped}"
            )
            
        except Exception as e:
            task.status = 'failed'
            task.errors.append(str(e))
            self.logger.error(f"Task {task.id} failed: {str(e)}")
            
        finally:
            # Cleanup
            if proxy:
                await self.proxy_manager.release_proxy(proxy)
            await self._cleanup_task(task)

    async def _scrape_with_retries(
        self, 
        spider: JewelrySpiderBase,
        proxy: Optional[str],
        max_retries: int,
        rate_limit: float
    ) -> List[Dict]:
        """Execute scraping with retry logic"""
        results = []
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Configure spider
                if proxy:
                    spider.set_proxy(proxy)
                
                # Execute scraping
                batch_results = await spider.run()
                results.extend(batch_results)
                
                # Break if successful
                break
                
            except Exception as e:
                retry_count += 1
                self.logger.warning(
                    f"Scraping attempt {retry_count} failed: {str(e)}"
                )
                
                if retry_count >= max_retries:
                    raise
                
                # Wait before retry
                await asyncio.sleep(retry_count * rate_limit)
                
                # Get new proxy if needed
                if proxy:
                    proxy = await self.proxy_manager.get_proxy()
                    
        return results

    async def _process_results(
        self,
        results: List[Dict],
        task: ScrapingTask
    ) -> List[Dict]:
        """Process and store scraped results"""
        processed_results = []
        
        for item in results:
            try:
                # Process images
                if item.get('image_urls'):
                    item['images'] = await self.image_processor.process_images(
                        urls=item['image_urls'],
                        product_id=str(task.id)
                    )
                
                # Store in database
                product_id = await self.db.add_product(item)
                if product_id:
                    item['id'] = product_id
                    processed_results.append(item)
                    task.items_scraped += 1
                
            except Exception as e:
                task.errors.append(f"Failed to process item: {str(e)}")
                self.logger.error(f"Error processing item: {str(e)}")
                
        return processed_results

    def _update_task_progress(self, task: ScrapingTask, stats: Dict):
        """Update task progress and monitoring"""
        try:
            # Update task stats
            task.items_scraped = stats.get('items_scraped', task.items_scraped)
            
            # Update monitoring
            self.monitor.track_progress(task.id, stats)
            
        except Exception as e:
            self.logger.error(f"Error updating progress: {str(e)}")

    async def _cleanup_task(self, task: ScrapingTask):
        """Perform task cleanup"""
        try:
            # Update monitoring
            self.monitor.track_completion(task.id, {
                'status': task.status,
                'items_scraped': task.items_scraped,
                'errors': len(task.errors),
                'duration': (datetime.now() - task.start_time).total_seconds()
            })
            
            # Cleanup temp files if needed
            if task.status != 'completed':
                await self.image_processor.cleanup_task_files(task.id)
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of a task"""
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
        """Cleanup resources"""
        try:
            # Cancel active tasks
            for task in self.active_tasks.values():
                if task.status == 'running':
                    task.status = 'cancelled'
            
            # Cleanup resources
            await self.proxy_manager.cleanup()
            await self.image_processor.cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
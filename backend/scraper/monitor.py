# File: /backend/scraper/monitor.py

import psutil
import time
from collections import deque
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio
from datetime import datetime, timedelta

@dataclass
class ScrapingMetrics:
    """Container for scraping performance metrics"""
    success_rate: float
    avg_response_time: float
    memory_usage: float
    cpu_usage: float
    active_jobs: int
    items_per_minute: float
    bandwidth_usage: float
    error_count: int

class ScraperMonitor:
    """Monitor scraping performance and resource usage"""

    def __init__(self, window_size: int = 100):
        # Performance tracking
        self.response_times = deque(maxlen=window_size)
        self.success_counts = deque(maxlen=window_size)
        self.error_counts = deque(maxlen=window_size)
        self.items_scraped = deque(maxlen=window_size)
        self.bandwidth_usage = deque(maxlen=window_size)
        
        # Resource tracking
        self.process = psutil.Process()
        self.start_time = time.time()
        
        # Job tracking
        self.active_jobs: Dict[str, Dict] = {}

    async def track_job(self, job_id: str, stats: Dict):
        """Update job statistics"""
        self.active_jobs[job_id] = {
            'start_time': datetime.now(),
            'items_scraped': stats.get('items_scraped', 0),
            'errors': stats.get('errors', 0),
            'bandwidth': stats.get('bandwidth', 0)
        }

        # Update global metrics
        self.items_scraped.append(stats.get('items_scraped', 0))
        self.bandwidth_usage.append(stats.get('bandwidth', 0))
        
        if response_time := stats.get('response_time'):
            self.response_times.append(response_time)
            
        success = not stats.get('errors', 0)
        self.success_counts.append(1 if success else 0)
        if not success:
            self.error_counts.append(1)

    def get_metrics(self) -> ScrapingMetrics:
        """Calculate current performance metrics"""
        try:
            # Calculate success rate
            success_rate = (
                sum(self.success_counts) / len(self.success_counts) * 100
                if self.success_counts else 100
            )

            # Calculate average response time
            avg_response = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )

            # Calculate items per minute
            elapsed_minutes = (time.time() - self.start_time) / 60
            items_per_min = sum(self.items_scraped) / elapsed_minutes if elapsed_minutes > 0 else 0

            # Get system metrics
            memory_percent = self.process.memory_percent()
            cpu_percent = self.process.cpu_percent()

            # Calculate bandwidth usage (MB/s)
            bandwidth = sum(self.bandwidth_usage) / (1024 * 1024)

            return ScrapingMetrics(
                success_rate=success_rate,
                avg_response_time=avg_response,
                memory_usage=memory_percent,
                cpu_usage=cpu_percent,
                active_jobs=len(self.active_jobs),
                items_per_minute=items_per_min,
                bandwidth_usage=bandwidth,
                error_count=sum(self.error_counts)
            )

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return None

    def cleanup_jobs(self, max_age: timedelta = timedelta(hours=1)):
        """Remove old completed jobs"""
        current_time = datetime.now()
        to_remove = []
        
        for job_id, job_data in self.active_jobs.items():
            if current_time - job_data['start_time'] > max_age:
                to_remove.append(job_id)
                
        for job_id in to_remove:
            del self.active_jobs[job_id]

    async def monitor_resources(self, threshold: float = 90.0):
        """Monitor system resources and alert on high usage"""
        while True:
            metrics = self.get_metrics()
            if metrics:
                if metrics.memory_usage > threshold:
                    logger.warning(f"High memory usage: {metrics.memory_usage:.1f}%")
                if metrics.cpu_usage > threshold:
                    logger.warning(f"High CPU usage: {metrics.cpu_usage:.1f}%")
                    
            await asyncio.sleep(60)  # Check every minute

    def get_job_stats(self, job_id: str) -> Optional[Dict]:
        """Get statistics for specific job"""
        if job_id not in self.active_jobs:
            return None
            
        job_data = self.active_jobs[job_id]
        elapsed = datetime.now() - job_data['start_time']
        
        return {
            'duration': str(elapsed),
            'items_scraped': job_data['items_scraped'],
            'errors': job_data['errors'],
            'bandwidth': job_data['bandwidth'],
            'items_per_minute': (
                job_data['items_scraped'] / (elapsed.total_seconds() / 60)
                if elapsed.total_seconds() > 0 else 0
            )
        }

    def get_summary(self) -> Dict:
        """Get overall scraping summary"""
        metrics = self.get_metrics()
        if not metrics:
            return {}
            
        return {
            'performance': {
                'success_rate': f"{metrics.success_rate:.1f}%",
                'avg_response': f"{metrics.avg_response_time:.2f}ms",
                'items_per_minute': f"{metrics.items_per_minute:.1f}"
            },
            'resources': {
                'memory': f"{metrics.memory_usage:.1f}%",
                'cpu': f"{metrics.cpu_usage:.1f}%",
                'bandwidth': f"{metrics.bandwidth_usage:.2f}MB/s"
            },
            'activity': {
                'active_jobs': metrics.active_jobs,
                'total_errors': metrics.error_count,
                'uptime': str(timedelta(seconds=int(time.time() - self.start_time)))
            }
        }
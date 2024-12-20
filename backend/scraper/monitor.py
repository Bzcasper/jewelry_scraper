import psutil
import time
from collections import deque
from typing import Dict, List
import asyncio
from dataclasses import dataclass
import statistics

@dataclass
class ScraperMetrics:
    success_rate: float
    avg_response_time: float
    memory_usage: float
    cpu_usage: float
    active_jobs: int
    items_per_minute: float
    errors_count: int
    bandwidth_usage: float

class ScraperMonitor:
    """Real-time monitoring and performance tracking"""

    def __init__(self, window_size: int = 100):
        self.response_times = deque(maxlen=window_size)
        self.success_counts = deque(maxlen=window_size)
        self.error_counts = deque(maxlen=window_size)
        self.items_scraped = deque(maxlen=window_size)
        self.bandwidth_usage = deque(maxlen=window_size)
        
        self.start_time = time.time()
        self.process = psutil.Process()

    def add_response_time(self, time_ms: float):
        """Track response time"""
        self.response_times.append(time_ms)

    def add_result(self, success: bool, items_count: int, bytes_transferred: int):
        """Track scraping result"""
        self.success_counts.append(1 if success else 0)
        self.items_scraped.append(items_count)
        self.bandwidth_usage.append(bytes_transferred)

    def add_error(self, error_type: str):
        """Track error occurrence"""
        self.error_counts.append(1)

    def get_metrics(self) -> ScraperMetrics:
        """Calculate current metrics"""
        try:
            # Calculate success rate
            success_rate = (
                statistics.mean(self.success_counts) * 100 
                if self.success_counts else 100
            )

            # Calculate average response time
            avg_response = (
                statistics.mean(self.response_times) 
                if self.response_times else 0
            )

            # Calculate items per minute
            items_per_min = sum(self.items_scraped) / (
                (time.time() - self.start_time) / 60
            )

            # Get system metrics
            memory_percent = self.process.memory_percent()
            cpu_percent = self.process.cpu_percent()

            # Calculate bandwidth usage (MB/s)
            bandwidth = sum(self.bandwidth_usage) / (1024 * 1024)

            return ScraperMetrics(
                success_rate=success_rate,
                avg_response_time=avg_response,
                memory_usage=memory_percent,
                cpu_usage=cpu_percent,
                active_jobs=len(self.success_counts),
                items_per_minute=items_per_min,
                errors_count=sum(self.error_counts),
                bandwidth_usage=bandwidth
            )

        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return None

    async def monitor_performance(self, interval: int = 60):
        """Continuous performance monitoring"""
        while True:
            metrics = self.get_metrics()
            if metrics:
                # Log performance alerts
                if metrics.memory_usage > 80:
                    print("WARNING: High memory usage")
                if metrics.cpu_usage > 70:
                    print("WARNING: High CPU usage")
                if metrics.success_rate < 90:
                    print("WARNING: Low success rate")

            await asyncio.sleep(interval)

    def generate_report(self) -> Dict:
        """Generate detailed performance report"""
        metrics = self.get_metrics()
        if not metrics:
            return {}

        return {
            'performance': {
                'success_rate': f"{metrics.success_rate:.2f}%",
                'avg_response_time': f"{metrics.avg_response_time:.2f}ms",
                'items_per_minute': f"{metrics.items_per_minute:.2f}"
            },
            'resources': {
                'memory_usage': f"{metrics.memory_usage:.2f}%",
                'cpu_usage': f"{metrics.cpu_usage:.2f}%",
                'bandwidth': f"{metrics.bandwidth_usage:.2f}MB/s"
            },
            'errors': {
                'total_errors': metrics.errors_count,
                'error_rate': f"{(metrics.errors_count / len(self.success_counts)) * 100:.2f}%"
                if self.success_counts else "0%"
            }
        }
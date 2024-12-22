import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
from dataclasses import dataclass
import time

@dataclass
class RateLimit:
    requests: int  # Number of requests
    period: int   # Time period in seconds
    current_count: int = 0
    last_reset: datetime = None

    def should_reset(self) -> bool:
        """Check if period has elapsed and count should reset"""
        if not self.last_reset:
            return True
        return datetime.now() - self.last_reset > timedelta(seconds=self.period)

    def reset(self):
        """Reset counter"""
        self.current_count = 0
        self.last_reset = datetime.now()

class AdaptiveRateLimiter:
    """Rate limiter with adaptive delays based on response success"""
    
    def __init__(self, base_delay: float = 1.0):
        self.limits: Dict[str, RateLimit] = {
            'default': RateLimit(requests=30, period=60),  # 30 requests per minute
            'ebay': RateLimit(requests=20, period=60),     # 20 requests per minute
            'amazon': RateLimit(requests=15, period=60)    # 15 requests per minute
        }
        self.base_delay = base_delay
        self.success_rate = 1.0
        self.last_request_time: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)

    async def wait(self, domain: str = 'default'):
        """Wait for rate limit with adaptive delay"""
        limit = self.limits.get(domain, self.limits['default'])
        
        # Check if period should reset
        if limit.should_reset():
            limit.reset()

        # Calculate adaptive delay
        delay = self.base_delay * (1 + (1 - self.success_rate))
        
        # Enforce minimum delay between requests
        if domain in self.last_request_time:
            time_since_last = datetime.now() - self.last_request_time[domain]
            if time_since_last.total_seconds() < delay:
                additional_delay = delay - time_since_last.total_seconds()
                await asyncio.sleep(additional_delay)

        # Check rate limit
        while limit.current_count >= limit.requests:
            time_to_wait = (limit.last_reset + timedelta(seconds=limit.period) - datetime.now()).total_seconds()
            if time_to_wait > 0:
                self.logger.warning(f"Rate limit reached for {domain}, waiting {time_to_wait:.2f}s")
                await asyncio.sleep(time_to_wait)
            limit.reset()

        # Update tracking
        limit.current_count += 1
        self.last_request_time[domain] = datetime.now()

    def update_success_rate(self, success: bool):
        """Update success rate for adaptive delay"""
        # Exponential moving average
        alpha = 0.1  # Smoothing factor
        self.success_rate = (1 - alpha) * self.success_rate + alpha * (1.0 if success else 0.0)

    def get_domain_stats(self, domain: str = 'default') -> Dict:
        """Get rate limiting stats for domain"""
        limit = self.limits.get(domain, self.limits['default'])
        return {
            'requests_remaining': limit.requests - limit.current_count,
            'period_remaining': (
                limit.last_reset + timedelta(seconds=limit.period) - datetime.now()
            ).total_seconds() if limit.last_reset else limit.period,
            'current_delay': self.base_delay * (1 + (1 - self.success_rate)),
            'success_rate': self.success_rate
        }

class BatchRateLimiter:
    """Rate limiter for batch operations"""
    
    def __init__(self, batch_size: int = 10, delay: float = 1.0):
        self.batch_size = batch_size
        self.delay = delay
        self.current_batch = 0
        self.last_batch_time: Optional[datetime] = None

    async def wait(self):
        """Wait between batches"""
        self.current_batch += 1
        
        if self.current_batch >= self.batch_size:
            if self.last_batch_time:
                time_since_last = datetime.now() - self.last_batch_time
                if time_since_last.total_seconds() < self.delay:
                    await asyncio.sleep(self.delay - time_since_last.total_seconds())
            
            self.current_batch = 0
            self.last_batch_time = datetime.now()

class TokenBucketRateLimiter:
    """Token bucket rate limiter for fine-grained control"""
    
    def __init__(self, tokens: int, interval: float):
        self.tokens = tokens
        self.interval = interval
        self.available_tokens = tokens
        self.last_update = time.time()

    async def acquire(self, tokens: int = 1):
        """Acquire tokens from the bucket"""
        while self.available_tokens < tokens:
            now = time.time()
            time_passed = now - self.last_update
            new_tokens = int(time_passed / self.interval * self.tokens)
            
            if new_tokens > 0:
                self.available_tokens = min(
                    self.available_tokens + new_tokens,
                    self.tokens
                )
                self.last_update = now
            
            if self.available_tokens < tokens:
                await asyncio.sleep(self.interval)

        self.available_tokens -= tokens
# File: /backend/utils/rate_limiter.py

from dataclasses import dataclass
import time
import asyncio
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

@dataclass
class RateLimit:
    """Configuration for rate limiting"""
    requests: int
    period: int  # seconds
    current_count: int = 0
    last_reset: Optional[datetime] = None

    def should_reset(self) -> bool:
        """Check if period has elapsed"""
        if not self.last_reset:
            return True
        return datetime.now() - self.last_reset > timedelta(seconds=self.period)

    def reset(self):
        """Reset counter"""
        self.current_count = 0
        self.last_reset = datetime.now()

class AdaptiveRateLimiter:
    """Rate limiter with adaptive delays based on server response"""
    
    def __init__(self):
        # Platform-specific limits
        self.limits = {
            'default': RateLimit(requests=30, period=60),  # 30 requests per minute
            'ebay': RateLimit(requests=20, period=60),     # 20 requests per minute
            'amazon': RateLimit(requests=15, period=60)    # 15 requests per minute
        }
        
        self.success_rate = 1.0  # Tracks success rate for adaptive delays
        self.base_delay = 1.0    # Base delay between requests
        self.last_request = {}   # Track last request time per domain
        
        self.logger = logging.getLogger(__name__)

    async def wait(self, domain: str = 'default'):
        """Wait appropriate time before next request"""
        limit = self.limits.get(domain, self.limits['default'])
        
        # Reset period if needed
        if limit.should_reset():
            limit.reset()

        # Calculate adaptive delay
        delay = self.base_delay * (1 + (1 - self.success_rate))
        
        # Check minimum time between requests
        if domain in self.last_request:
            time_since_last = datetime.now() - self.last_request[domain]
            if time_since_last.total_seconds() < delay:
                await asyncio.sleep(delay - time_since_last.total_seconds())

        # Check rate limit
        while limit.current_count >= limit.requests:
            # Wait until next period
            time_until_reset = (
                limit.last_reset + timedelta(seconds=limit.period) - datetime.now()
            ).total_seconds()
            
            if time_until_reset > 0:
                self.logger.warning(
                    f"Rate limit reached for {domain}, waiting {time_until_reset:.2f}s"
                )
                await asyncio.sleep(time_until_reset)
            limit.reset()

        # Update tracking
        limit.current_count += 1
        self.last_request[domain] = datetime.now()

    def update_success_rate(self, success: bool):
        """Update success rate for adaptive delay"""
        # Use exponential moving average
        alpha = 0.1  # Smoothing factor
        self.success_rate = (1 - alpha) * self.success_rate + alpha * float(success)

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
    """Token bucket algorithm for precise rate limiting"""
    
    def __init__(self, tokens: int, interval: float):
        self.tokens = tokens
        self.interval = interval
        self.available_tokens = tokens
        self.last_updated = time.time()

    async def acquire(self, tokens: int = 1):
        """Acquire tokens for request"""
        while self.available_tokens < tokens:
            now = time.time()
            time_passed = now - self.last_updated
            
            # Calculate new tokens
            new_tokens = int(time_passed / self.interval * self.tokens)
            if new_tokens > 0:
                self.available_tokens = min(
                    self.available_tokens + new_tokens,
                    self.tokens
                )
                self.last_updated = now
            
            if self.available_tokens < tokens:
                await asyncio.sleep(self.interval)

        self.available_tokens -= tokens
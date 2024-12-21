# File: /backend/utils/proxy_manager.py

import aiohttp
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import random
from pathlib import Path

@dataclass
class Proxy:
    """Proxy configuration and health metrics"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    last_used: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    response_time: float = 0.0
    country: Optional[str] = None

    @property
    def url(self) -> str:
        """Get formatted proxy URL"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

    @property
    def health_score(self) -> float:
        """Calculate proxy health score (0-1)"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5
        return self.success_count / total

class ProxyManager:
    """Manages proxy rotation and health monitoring"""

    def __init__(self, config_path: Optional[Path] = None):
        self.proxies: List[Proxy] = []
        self.config_path = config_path or Path("config/proxies.json")
        self.test_url = "https://api.ipify.org?format=json"
        self.min_health_score = 0.3
        self.max_consecutive_fails = 3
        self.rotation_delay = timedelta(seconds=30)
        
        self._load_proxies()

    def _load_proxies(self):
        """Load proxies from configuration file"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    proxy_list = json.load(f)
                self.proxies = [Proxy(**p) for p in proxy_list]
            except Exception as e:
                logger.error(f"Failed to load proxies: {e}")

    async def get_proxy(self) -> Optional[Proxy]:
        """Get next best available proxy"""
        if not self.proxies:
            return None

        # Filter available proxies
        available = [
            p for p in self.proxies
            if p.health_score >= self.min_health_score
            and (not p.last_used or
                 datetime.now() - p.last_used > self.rotation_delay)
        ]

        if not available:
            return None

        # Select proxy based on health score and response time
        proxy = max(
            available,
            key=lambda p: p.health_score / (p.response_time + 0.1)
        )
        
        proxy.last_used = datetime.now()
        return proxy

    async def test_proxy(self, proxy: Proxy) -> bool:
        """Test proxy connectivity and response time"""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy.url,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        proxy.response_time = time.time() - start_time
                        proxy.success_count += 1
                        return True
                    
            proxy.fail_count += 1
            return False
            
        except Exception as e:
            logger.warning(f"Proxy test failed for {proxy.host}: {e}")
            proxy.fail_count += 1
            return False

    async def validate_proxies(self):
        """Test all proxies and remove unhealthy ones"""
        tasks = [self.test_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)
        
        # Update proxy list
        self.proxies = [
            proxy for proxy, is_valid in zip(self.proxies, results)
            if is_valid and proxy.health_score >= self.min_health_score
        ]

    def report_success(self, proxy: Proxy):
        """Report successful proxy use"""
        proxy.success_count += 1
        proxy.last_used = datetime.now()

    def report_failure(self, proxy: Proxy):
        """Report proxy failure"""
        proxy.fail_count += 1
        
        # Remove proxy if too many failures
        if (proxy.fail_count >= self.max_consecutive_fails or
            proxy.health_score < self.min_health_score):
            self.proxies.remove(proxy)

    async def rotate_proxy(self, current: Optional[Proxy] = None) -> Optional[Proxy]:
        """Get new proxy, avoiding the current one"""
        if current:
            current.last_used = datetime.now()
        
        return await self.get_proxy()

    def save_state(self):
        """Save proxy configurations and statistics"""
        try:
            proxy_data = [
                {
                    'host': p.host,
                    'port': p.port,
                    'username': p.username,
                    'password': p.password,
                    'protocol': p.protocol,
                    'country': p.country,
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                    'response_time': p.response_time
                }
                for p in self.proxies
            ]
            
            with open(self.config_path, 'w') as f:
                json.dump(proxy_data, f, indent=2)
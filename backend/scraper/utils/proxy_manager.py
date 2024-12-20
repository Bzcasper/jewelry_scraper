from typing import Optional, List, Dict
import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
import json
from dataclasses import dataclass
import random

@dataclass
class Proxy:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = 'http'
    last_used: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    response_time: float = 0.0

    @property
    def url(self) -> str:
        """Get formatted proxy URL"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

    @property
    def health_score(self) -> float:
        """Calculate proxy health score (0-1)"""
        if self.success_count + self.fail_count == 0:
            return 0.5
        return self.success_count / (self.success_count + self.fail_count)

class ProxyManager:
    def __init__(self, proxy_file: str = "config/proxies.json"):
        self.proxies: List[Proxy] = []
        self.current_index: int = 0
        self.proxy_file = proxy_file
        self.test_url = "https://api.ipify.org?format=json"
        self.min_delay = 5  # Minimum seconds between reusing a proxy
        self.logger = logging.getLogger(__name__)

        # Load proxies
        self.load_proxies()

    def load_proxies(self):
        """Load proxies from configuration file"""
        try:
            with open(self.proxy_file, 'r') as f:
                proxy_list = json.load(f)
                self.proxies = [Proxy(**proxy) for proxy in proxy_list]
            self.logger.info(f"Loaded {len(self.proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Failed to load proxies: {e}")
            # Load fallback proxies if available
            self.load_fallback_proxies()

    def load_fallback_proxies(self):
        """Load basic fallback proxies"""
        fallback_proxies = [
            {"host": "proxy1.example.com", "port": 8080},
            {"host": "proxy2.example.com", "port": 8080}
        ]
        self.proxies = [Proxy(**proxy) for proxy in fallback_proxies]

    async def get_proxy(self) -> Optional[Proxy]:
        """Get next available proxy with health check"""
        if not self.proxies:
            return None

        # Sort proxies by health score and last used time
        available_proxies = [
            p for p in self.proxies
            if not p.last_used or 
            datetime.now() - p.last_used > timedelta(seconds=self.min_delay)
        ]

        if not available_proxies:
            self.logger.warning("No proxies currently available")
            await asyncio.sleep(self.min_delay)
            return await self.get_proxy()

        # Sort by health score
        available_proxies.sort(key=lambda p: p.health_score, reverse=True)
        
        # Get top 3 healthiest proxies and choose randomly
        top_proxies = available_proxies[:3]
        proxy = random.choice(top_proxies)
        
        # Update last used time
        proxy.last_used = datetime.now()
        return proxy

    async def test_proxy(self, proxy: Proxy) -> bool:
        """Test proxy connectivity"""
        try:
            start_time = datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.test_url,
                    proxy=proxy.url,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds()
                        proxy.response_time = response_time
                        proxy.success_count += 1
                        return True
                    
            proxy.fail_count += 1
            return False
        except Exception as e:
            self.logger.warning(f"Proxy test failed for {proxy.host}: {e}")
            proxy.fail_count += 1
            return False

    async def verify_proxies(self):
        """Verify all proxies in parallel"""
        tasks = [self.test_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Remove failed proxies
        self.proxies = [
            proxy for proxy, result in zip(self.proxies, results)
            if isinstance(result, bool) and result
        ]
        
        self.logger.info(f"Verified {len(self.proxies)} working proxies")

    def report_success(self, proxy: Proxy):
        """Report successful proxy use"""
        proxy.success_count += 1
        proxy.last_used = datetime.now()

    def report_failure(self, proxy: Proxy):
        """Report proxy failure"""
        proxy.fail_count += 1
        if proxy.health_score < 0.2:  # Remove proxies with poor health
            self.proxies.remove(proxy)
            self.logger.info(f"Removed unhealthy proxy {proxy.host}")

    async def rotate_proxy(self, current_proxy: Optional[Proxy] = None) -> Optional[Proxy]:
        """Rotate to next proxy"""
        if current_proxy:
            current_proxy.last_used = datetime.now()
        return await self.get_proxy()

    def save_proxy_stats(self):
        """Save proxy statistics"""
        try:
            proxy_stats = [
                {
                    'host': p.host,
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                    'response_time': p.response_time,
                    'health_score': p.health_score
                }
                for p in self.proxies
            ]
            with open('logs/proxy_stats.json', 'w') as f:
                json.dump(proxy_stats, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save proxy stats: {e}")
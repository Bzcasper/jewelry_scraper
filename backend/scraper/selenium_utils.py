import os
import random
import time
import json
import logging
from typing import Optional, Dict, List, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    SessionNotCreatedException
)
from selenium.webdriver.common.proxy import Proxy, ProxyType
import requests
from fake_useragent import UserAgent
import aiohttp
import asyncio
from functools import wraps
import platform

@dataclass
class ProxyConfig:
    """Configuration for proxy settings"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    country: Optional[str] = None
    last_used: Optional[datetime] = None
    success_rate: float = 0.0
    response_time: float = 0.0
    fail_count: int = 0

class EnhancedProxyManager:
    def __init__(self, proxy_list_path: Optional[str] = None):
        self.proxies: List[ProxyConfig] = []
        self.user_agent = UserAgent()
        self.load_proxies(proxy_list_path)
        self.min_proxy_rotation_interval = timedelta(seconds=30)
        self.max_fails = 3
        self.testing_url = "https://www.google.com"
        self.proxy_test_timeout = 10

    def load_proxies(self, proxy_list_path: Optional[str] = None):
        """Load proxies from file or environment variables"""
        if proxy_list_path and os.path.exists(proxy_list_path):
            with open(proxy_list_path, 'r') as f:
                proxy_list = json.load(f)
                self.proxies = [ProxyConfig(**p) for p in proxy_list]
        else:
            # Load from environment variables
            proxy_str = os.getenv('PROXY_LIST', '')
            if proxy_str:
                proxy_list = json.loads(proxy_str)
                self.proxies = [ProxyConfig(**p) for p in proxy_list]

    async def test_proxy(self, proxy: ProxyConfig) -> bool:
        """Test proxy connectivity asynchronously"""
        proxy_url = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
        auth = aiohttp.BasicAuth(proxy.username, proxy.password) if proxy.username else None

        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.testing_url,
                    proxy=proxy_url,
                    proxy_auth=auth,
                    timeout=self.proxy_test_timeout
                ) as response:
                    if response.status == 200:
                        elapsed = time.time() - start_time
                        proxy.response_time = elapsed
                        proxy.success_rate = (proxy.success_rate * 9 + 1) / 10
                        return True
        except Exception as e:
            logging.warning(f"Proxy test failed for {proxy_url}: {str(e)}")
            proxy.fail_count += 1
            proxy.success_rate = (proxy.success_rate * 9) / 10
            return False

    async def test_all_proxies(self):
        """Test all proxies concurrently"""
        tasks = [self.test_proxy(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)
        
        # Remove failed proxies
        self.proxies = [
            proxy for proxy, result in zip(self.proxies, results)
            if result and proxy.fail_count < self.max_fails
        ]

    def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get the next best available proxy"""
        if not self.proxies:
            return None

        # Sort proxies by success rate and response time
        valid_proxies = [
            p for p in self.proxies
            if (not p.last_used or 
                datetime.now() - p.last_used > self.min_proxy_rotation_interval)
            and p.fail_count < self.max_fails
        ]

        if not valid_proxies:
            return None

        # Select best proxy based on success rate and response time
        best_proxy = max(
            valid_proxies,
            key=lambda p: p.success_rate / (p.response_time + 0.1)
        )
        
        best_proxy.last_used = datetime.now()
        return best_proxy

    def mark_proxy_failed(self, proxy: ProxyConfig):
        """Mark a proxy as failed"""
        if proxy in self.proxies:
            proxy.fail_count += 1
            proxy.success_rate = (proxy.success_rate * 9) / 10
            if proxy.fail_count >= self.max_fails:
                self.proxies.remove(proxy)

class WebDriverManager:
    def __init__(self, proxy_manager: EnhancedProxyManager):
        self.proxy_manager = proxy_manager
        self.driver_path = self._get_driver_path()
        self.max_retries = 3
        self.page_load_timeout = 30
        self.default_wait_timeout = 10

    def _get_driver_path(self) -> str:
        """Get the appropriate ChromeDriver path for the current platform"""
        system = platform.system().lower()
        if system == "windows":
            return os.environ.get("CHROME_DRIVER_PATH", "chromedriver.exe")
        return os.environ.get("CHROME_DRIVER_PATH", "chromedriver")

    def _setup_chrome_options(self, proxy: Optional[ProxyConfig] = None) -> Options:
        """Setup Chrome options with enhanced security and performance settings"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Random user agent
        options.add_argument(f"user-agent={self.proxy_manager.user_agent.random}")

        # Add proxy if provided
        if proxy:
            proxy_str = f"{proxy.protocol}://{proxy.host}:{proxy.port}"
            if proxy.username and proxy.password:
                auth = f"{proxy.username}:{proxy.password}@"
                proxy_str = proxy_str.replace("://", f"://{auth}")
            options.add_argument(f"--proxy-server={proxy_str}")

        return options

    def create_driver(self, proxy: Optional[ProxyConfig] = None) -> webdriver.Chrome:
        """Create a new Chrome driver with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                service = Service(executable_path=self.driver_path)
                options = self._setup_chrome_options(proxy)
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(self.page_load_timeout)
                
                # Basic browser automation detection evasion
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                })
                
                return driver
            except Exception as e:
                logging.error(f"Failed to create driver (attempt {attempt + 1}): {str(e)}")
                if proxy:
                    self.proxy_manager.mark_proxy_failed(proxy)
                    proxy = self.proxy_manager.get_next_proxy()
                if attempt == self.max_retries - 1:
                    raise

    def safe_get(self, driver: webdriver.Chrome, url: str, retries: int = 3) -> bool:
        """Safely navigate to a URL with retry mechanism"""
        for attempt in range(retries):
            try:
                driver.get(url)
                return True
            except TimeoutException:
                logging.warning(f"Timeout loading {url} (attempt {attempt + 1})")
                driver.execute_script("window.stop();")
            except Exception as e:
                logging.error(f"Error loading {url} (attempt {attempt + 1}): {str(e)}")
                if attempt == retries - 1:
                    return False
        return False

    def wait_for_element(
        self,
        driver: webdriver.Chrome,
        selector: str,
        by: By = By.CSS_SELECTOR,
        timeout: int = None
    ) -> bool:
        """Wait for an element to be present"""
        try:
            WebDriverWait(driver, timeout or self.default_wait_timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            return False

def save_html_backup(content: Union[str, webdriver.Chrome], filename: Optional[str] = None):
    """
    Save HTML content or current page source to a backup file with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = filename or f"backup_{timestamp}.html"
    
    backup_dir = os.path.join("backups", datetime.now().strftime("%Y%m%d"))
    os.makedirs(backup_dir, exist_ok=True)
    
    file_path = os.path.join(backup_dir, filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            if isinstance(content, webdriver.Chrome):
                f.write(content.page_source)
            else:
                f.write(content)
        logging.info(f"Backup saved to {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Failed to save backup: {str(e)}")
        return None

# Initialize managers
proxy_manager = EnhancedProxyManager()
driver_manager = WebDriverManager(proxy_manager)

def setup_driver_with_failover() -> Optional[webdriver.Chrome]:
    """
    Create a new web driver with proxy failover support
    """
    proxy = proxy_manager.get_next_proxy()
    try:
        driver = driver_manager.create_driver(proxy)
        return driver
    except Exception as e:
        logging.error(f"Failed to set up driver: {str(e)}")
        return None

# Async initialization
async def initialize_proxy_pool():
    """
    Initialize and test the proxy pool
    """
    await proxy_manager.test_all_proxies()

# Run proxy pool initialization
if __name__ == "__main__":
    asyncio.run(initialize_proxy_pool())
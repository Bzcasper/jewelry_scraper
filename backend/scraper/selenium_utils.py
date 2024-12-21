# File: /backend/scraper/selenium_utils.py

import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
from typing import Optional, Dict
import time
from pathlib import Path

class SeleniumManager:
    """Manage Selenium WebDriver instances with proxy support"""
    
    def __init__(self, headless: bool = True):
        self.logger = logging.getLogger(__name__)
        self.headless = headless
        self._setup_driver_path()

    def _setup_driver_path(self):
        """Setup ChromeDriver path based on environment"""
        if os.environ.get('CHROMEDRIVER_PATH'):
            self.driver_path = os.environ['CHROMEDRIVER_PATH']
        else:
            # Default paths based on OS
            if os.name == 'nt':  # Windows
                self.driver_path = 'chromedriver.exe'
            else:  # Unix/Linux/Mac
                self.driver_path = 'chromedriver'

    def create_driver(self, proxy: Optional[Dict] = None) -> uc.Chrome:
        """Create an undetected ChromeDriver instance"""
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Add proxy if provided
        if proxy:
            proxy_str = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
            if proxy.get('username') and proxy.get('password'):
                auth = f"{proxy['username']}:{proxy['password']}@"
                proxy_str = proxy_str.replace("://", f"://{auth}")
            options.add_argument(f'--proxy-server={proxy_str}')

        driver = uc.Chrome(
            executable_path=self.driver_path,
            options=options
        )
        
        # Configure timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        return driver

    @staticmethod
    def wait_for_element(driver: uc.Chrome, selector: str, timeout: int = 10) -> bool:
        """Wait for element to be present"""
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            return False

    @staticmethod
    def scroll_page(driver: uc.Chrome, pause: float = 1.0):
        """Scroll page to load dynamic content"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def save_screenshot(self, driver: uc.Chrome, name: str):
        """Save screenshot for debugging"""
        try:
            screenshots_dir = Path('logs/screenshots')
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{name}_{timestamp}.png"
            driver.save_screenshot(str(screenshots_dir / filename))
            
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
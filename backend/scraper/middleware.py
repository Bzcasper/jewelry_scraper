from scrapy import signals
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import asyncio
import aiohttp
from PIL import Image
import io
import logging
from urllib.parse import urljoin
import time

class DynamicContentMiddleware:
    """Middleware to handle dynamic content loading and image processing"""
    
    def __init__(self):
        self.driver = None
        self.image_semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads
        
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        # Initialize undetected-chromedriver to bypass detection
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Add headers to mimic real browser
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        spider.driver = self.driver
        spider.wait = self.wait

    def spider_closed(self, spider):
        if self.driver:
            self.driver.quit()

    async def process_page(self, url):
        """Process dynamic page content"""
        self.driver.get(url)
        
        # Wait for main content to load
        try:
            main_content = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.s-result-item, .s-item'))
            )
        except TimeoutException:
            logging.error(f"Timeout waiting for main content: {url}")
            return None

        # Scroll to load lazy content
        self.scroll_page()
        
        # Wait for dynamic elements
        self.wait_for_dynamic_elements()
        
        return self.driver.page_source

    def scroll_page(self):
        """Scroll page to trigger lazy loading"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # Allow time for content to load
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def wait_for_dynamic_elements(self):
        """Wait for specific dynamic elements to load"""
        try:
            # Wait for images to load
            self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'img[src]'))
            )
            # Wait for price elements
            self.wait.until(
                EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR, '.s-price, .price, .s-item__price'
                ))
            )
        except TimeoutException:
            logging.warning("Some dynamic elements failed to load")

    async def download_image(self, url: str, product_id: str) -> str:
        """Download and process product image asynchronously"""
        async with self.image_semaphore:  # Limit concurrent downloads
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            return await self.process_image(image_data, product_id, url)
            except Exception as e:
                logging.error(f"Error downloading image {url}: {e}")
                return None

    async def process_image(self, image_data: bytes, product_id: str, url: str) -> str:
        """Process and optimize downloaded image"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large while maintaining aspect ratio
            max_size = 1200
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, 
                      format='JPEG', 
                      quality=85, 
                      optimize=True)
            
            # Generate unique filename
            filename = f"{product_id}_{hash(url)}.jpg"
            
            # Save to storage
            with open(f"product_images/{filename}", 'wb') as f:
                f.write(output.getvalue())
            
            return filename
            
        except Exception as e:
            logging.error(f"Error processing image: {e}")
            return None
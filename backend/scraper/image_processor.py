from PIL import Image
import aiohttp
import asyncio
from io import BytesIO
import os
from typing import List, Dict, Optional
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import magic
import aiofiles
from concurrent.futures import ThreadPoolExecutor

class ImageProcessor:
    """Handles downloading, processing, and storing product images"""
    
    def __init__(self):
        # Configure storage paths
        self.base_path = Path('product_images')
        self.base_path.mkdir(exist_ok=True)
        
        # Image processing settings
        self.max_size = 1200
        self.quality = 85
        self.formats = {'.jpg', '.jpeg', '.png', '.webp'}
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(5)
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)

    async def process_images(self, urls: List[str], product_id: str) -> List[Dict]:
        """Process multiple product images concurrently"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        processed_images = []
        tasks = []

        # Create product directory
        product_dir = self.base_path / product_id
        product_dir.mkdir(exist_ok=True)

        # Process images concurrently
        for idx, url in enumerate(urls):
            task = self._process_single_image(
                url=url,
                product_id=product_id,
                is_primary=(idx == 0)
            )
            tasks.append(task)

        # Wait for all images to process
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in results:
            if isinstance(result, dict) and result.get('success'):
                processed_images.append(result)

        return processed_images

    async def _process_single_image(self, url: str, product_id: str, is_primary: bool) -> Dict:
        """Process a single image with error handling"""
        try:
            async with self.semaphore:
                # Download image
                image_data = await self._download_image(url)
                if not image_data:
                    return {'success': False, 'error': 'Download failed'}

                # Validate image
                if not self._validate_image(image_data):
                    return {'success': False, 'error': 'Invalid image'}

                # Generate filename
                filename = self._generate_filename(url, product_id)
                filepath = self.base_path / product_id / filename

                # Process image in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    self._optimize_image,
                    image_data,
                    filepath
                )

                if not result:
                    return {'success': False, 'error': 'Processing failed'}

                return {
                    'success': True,
                    'url': url,
                    'local_path': str(filepath),
                    'is_primary': is_primary,
                    'size': filepath.stat().st_size,
                    'dimensions': result['dimensions']
                }

        except Exception as e:
            self.logger.error(f"Error processing image {url}: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image with retry logic"""
        for attempt in range(3):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if not content_type.startswith('image/'):
                            return None
                        
                        return await response.read()
                    
                    await asyncio.sleep(attempt + 1)
                    
            except Exception as e:
                self.logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    return None
                await asyncio.sleep(attempt + 1)

    def _validate_image(self, image_data: bytes) -> bool:
        """Validate image data"""
        try:
            # Check file type
            mime = magic.from_buffer(image_data, mime=True)
            if not mime.startswith('image/'):
                return False

            # Verify image can be opened
            image = Image.open(BytesIO(image_data))
            
            # Check dimensions
            if image.size[0] < 100 or image.size[1] < 100:
                return False

            # Check file size
            if len(image_data) > 10 * 1024 * 1024:  # 10MB
                return False

            return True

        except Exception:
            return False

    def _optimize_image(self, image_data: bytes, filepath: Path) -> Optional[Dict]:
        """Optimize image for storage"""
        try:
            image = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')

            # Resize if needed
            if max(image.size) > self.max_size:
                ratio = self.max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)

            # Optimize and save
            image.save(
                filepath,
                format='JPEG',
                quality=self.quality,
                optimize=True,
                progressive=True
            )

            return {
                'dimensions': image.size,
                'format': 'JPEG'
            }

        except Exception as e:
            self.logger.error(f"Error optimizing image: {str(e)}")
            return None

    def _generate_filename(self, url: str, product_id: str) -> str:
        """Generate unique filename for image"""
        # Create hash from URL and timestamp
        timestamp = datetime.now().isoformat()
        url_hash = hashlib.md5(f"{url}{timestamp}".encode()).hexdigest()[:10]
        
        return f"{product_id}_{url_hash}.jpg"

    async def cleanup_unused_images(self, active_paths: List[str]):
        """Remove unused images"""
        try:
            for product_dir in self.base_path.iterdir():
                if not product_dir.is_dir():
                    continue

                for image_file in product_dir.iterdir():
                    if str(image_file) not in active_paths:
                        try:
                            image_file.unlink()
                        except Exception as e:
                            self.logger.error(f"Error deleting {image_file}: {str(e)}")

                # Remove empty directories
                if not any(product_dir.iterdir()):
                    product_dir.rmdir()

        except Exception as e:
            self.logger.error(f"Error during image cleanup: {str(e)}")

    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=False)
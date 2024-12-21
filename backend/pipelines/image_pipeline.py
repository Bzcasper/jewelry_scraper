import scrapy
from scrapy.pipelines.images import ImagesPipeline
from PIL import Image
import hashlib
import os
import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional
from io import BytesIO

class JewelryImagePipeline(ImagesPipeline):
    """Enhanced pipeline for processing jewelry images"""

    def __init__(self, store_uri, download_func=None, settings=None):
        super().__init__(store_uri, download_func=download_func, settings=settings)
        self.min_width = 300  # Minimum image width
        self.min_height = 300  # Minimum image height
        self.max_size = 1200  # Maximum dimension
        self.semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads

    def get_media_requests(self, item, info):
        """Generate image download requests"""
        # Skip if no images
        if not item.get('image_urls'):
            return []
        
        # Deduplicate image URLs
        unique_urls = list(set(item['image_urls']))
        
        return [
            scrapy.Request(
                url,
                meta={
                    'product_id': item.get('id'),
                    'platform': item.get('platform'),
                    'image_index': idx
                }
            )
            for idx, url in enumerate(unique_urls)
        ]

    async def process_image(self, response, info):
        """Process downloaded image"""
        image = Image.open(BytesIO(response.body))
        
        # Validate image dimensions
        if image.size[0] < self.min_width or image.size[1] < self.min_height:
            raise ValueError(f"Image too small: {image.size}")
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if necessary
        if max(image.size) > self.max_size:
            ratio = self.max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.LANCZOS)
        
        # Optimize image
        output = BytesIO()
        image.save(
            output, 
            format='JPEG',
            quality=85,
            optimize=True,
            progressive=True
        )
        
        return output.getvalue()

    def file_path(self, request, response=None, info=None):
        """Generate file path for image storage"""
        # Create unique filename
        product_id = request.meta.get('product_id', '')
        platform = request.meta.get('platform', '')
        image_index = request.meta.get('image_index', 0)
        
        # Hash URL for unique identification
        url_hash = hashlib.md5(request.url.encode()).hexdigest()[:10]
        
        return f"{platform}/{product_id}/{url_hash}_{image_index}.jpg"

    async def handle_high_res_image(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Handle high-resolution image download"""
        try:
            async with self.semaphore:  # Limit concurrent downloads
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        return await self.process_image(data)
                    return None
        except Exception as e:
            logging.error(f"Error downloading high-res image {url}: {e}")
            return None

    def item_completed(self, results, item, info):
        """Process item after image downloads complete"""
        # Filter successful downloads
        image_paths = [x['path'] for ok, x in results if ok]
        
        if not image_paths:
            logging.warning(f"No images downloaded for product {item.get('id')}")
        
        # Update item with image paths
        item['image_paths'] = image_paths
        item['primary_image'] = image_paths[0] if image_paths else None
        
        return item
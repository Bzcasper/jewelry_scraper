import os

# Define imports for specific folders
default_imports = {
    "spiders": [
        "from .ebay_spider import EbayJewelrySpider",
        "from .amazon_spider import AmazonJewelrySpider",
        "from .base_spider import JewelrySpiderBase",
    ],
    "utils": [
        "from .image_processor import ImageProcessor",
        "from .proxy_manager import ProxyManager",
        "from .rate_limiter import RateLimiter",
    ],
    "database": [
        "from .db import Database",
        "from .models import Product",
        "from .backup import BackupManager",
        "from .manager import DatabaseManager",
    ],
    "api": [
        "from .app import app",
    ],
}

# Walk through directories and add __init__.py files
for root, dirs, files in os.walk("."):
    if "__pycache__" in root or ".git" in root:
        continue

    folder_name = os.path.basename(root)
    init_file_path = os.path.join(root, "__init__.py")

    # Skip if folder has no predefined imports
    if folder_name not in default_imports:
        continue

    # Write imports to __init__.py
    with open(init_file_path, "w") as init_file:
        init_file.write("\n".join(default_imports[folder_name]))
        print(f"Added imports to {init_file_path}")

# File: /backend/config/settings.py

from pydantic import BaseSettings, Field
from typing import List, Dict, Optional
from pathlib import Path
import json
from functools import lru_cache

class ScrapingSettings(BaseSettings):
    """Scraping configuration"""
    MAX_CONCURRENT_REQUESTS: int = 8
    REQUEST_TIMEOUT: int = 30
    RETRY_TIMES: int = 3
    RETRY_DELAY: int = 5
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ]
    
    EBAY_SETTINGS: Dict = {
        "rate_limit": 20,
        "categories": ["281"],  # Jewelry category IDs
        "max_items_per_search": 200
    }
    
    AMAZON_SETTINGS: Dict = {
        "rate_limit": 15,
        "categories": ["jewelry"],
        "max_items_per_search": 150
    }

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    URL: str = "sqlite:///jewelry_scraper.db"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    ECHO: bool = False
    BACKUP_DIR: str = "data/backups"

class ImageSettings(BaseSettings):
    """Image processing configuration"""
    STORAGE_PATH: str = "data/images"
    MAX_SIZE: int = 1200
    QUALITY: int = 85
    FORMATS: List[str] = ["JPEG", "PNG", "WEBP"]
    MIN_WIDTH: int = 500
    MIN_HEIGHT: int = 500
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

class APISettings(BaseSettings):
    """API configuration"""
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    JWT_SECRET: str = Field(default="", env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"

class Settings(BaseSettings):
    """Main application settings"""
    ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Component settings
    scraping: ScrapingSettings = ScrapingSettings()
    database: DatabaseSettings = DatabaseSettings()
    image: ImageSettings = ImageSettings()
    api: APISettings = APISettings()
    
    # Path settings
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_directories()
        self._load_environment_config()

    def _init_directories(self):
        """Initialize required directories"""
        dirs = [
            self.DATA_DIR / "images",
            self.DATA_DIR / "backups",
            self.LOG_DIR
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_environment_config(self):
        """Load environment-specific configuration"""
        env_file = self.BASE_DIR / f"config/{self.ENV}.json"
        if env_file.exists():
            with open(env_file) as f:
                self.update_settings(json.load(f))

    def update_settings(self, settings_dict: Dict):
        """Update settings from dictionary"""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                current_value = getattr(self, key)
                if isinstance(current_value, (DatabaseSettings, ScrapingSettings, 
                                           ImageSettings, APISettings)):
                    for k, v in value.items():
                        setattr(current_value, k, v)
                else:
                    setattr(self, key, value)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
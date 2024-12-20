from typing import Dict, Optional, List
from pathlib import Path
from pydantic import BaseSettings, Field
import json
import os
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    URL: str = "sqlite:///jewelry_scraper.db"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    ECHO: bool = False
    BACKUP_DIR: str = "data/backups"

class ScrapingSettings(BaseSettings):
    """Scraping configuration settings"""
    MAX_CONCURRENT_REQUESTS: int = 8
    REQUEST_TIMEOUT: int = 30
    RETRY_TIMES: int = 3
    RETRY_DELAY: int = 5
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36"
    ]
    
    # Platform-specific settings
    EBAY_SETTINGS: Dict = {
        "rate_limit": 20,  # requests per minute
        "categories": ["281"],  # jewelry category IDs
        "max_items_per_search": 200
    }
    
    AMAZON_SETTINGS: Dict = {
        "rate_limit": 15,  # requests per minute
        "categories": ["jewelry"],
        "max_items_per_search": 150
    }

class ProxySettings(BaseSettings):
    """Proxy configuration settings"""
    PROXY_FILE: str = "config/proxies.json"
    PROXY_TEST_URL: str = "https://api.ipify.org?format=json"
    MIN_PROXY_SCORE: float = 0.5
    PROXY_TIMEOUT: int = 10
    PROXY_ROTATION_INTERVAL: int = 300  # 5 minutes

class ImageSettings(BaseSettings):
    """Image processing configuration settings"""
    STORAGE_PATH: str = "data/images"
    MAX_SIZE: int = 1200
    QUALITY: int = 85
    FORMATS: List[str] = ["JPEG", "PNG", "WEBP"]
    MIN_WIDTH: int = 500
    MIN_HEIGHT: int = 500
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

class APISettings(BaseSettings):
    """API configuration settings"""
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_IN: int = 3600  # 1 hour

class LoggingSettings(BaseSettings):
    """Logging configuration settings"""
    LEVEL: str = "INFO"
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE: str = "logs/app.log"
    MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5
    MAIL_ERRORS: bool = True
    ERROR_MAIL_SETTINGS: Dict = {
        "host": "smtp.gmail.com",
        "port": 587,
        "username": "your-email@gmail.com",
        "password": "your-app-password",
        "to_addresses": ["admin@example.com"]
    }

class Settings(BaseSettings):
    """Main configuration settings"""
    # Environment
    ENV: str = Field(default="development", env="APP_ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    TESTING: bool = Field(default=False, env="TESTING")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    scraping: ScrapingSettings = ScrapingSettings()
    proxy: ProxySettings = ProxySettings()
    image: ImageSettings = ImageSettings()
    api: APISettings = APISettings()
    logging: LoggingSettings = LoggingSettings()

    # Path settings
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"
    CONFIG_DIR: Path = BASE_DIR / "config"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_directories()
        self._load_environment_specific()

    def _init_directories(self):
        """Initialize required directories"""
        directories = [
            self.DATA_DIR,
            self.DATA_DIR / "images",
            self.DATA_DIR / "backups",
            self.LOG_DIR,
            self.CONFIG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_environment_specific(self):
        """Load environment-specific settings"""
        env_file = self.CONFIG_DIR / f"{self.ENV}.json"
        if env_file.exists():
            with open(env_file) as f:
                env_settings = json.load(f)
                for key, value in env_settings.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

    def get_proxy_list(self) -> List[Dict]:
        """Load proxy list from configuration"""
        proxy_file = self.CONFIG_DIR / self.proxy.PROXY_FILE
        if proxy_file.exists():
            with open(proxy_file) as f:
                return json.load(f)
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Environment-specific configuration files
DEVELOPMENT_CONFIG = {
    "api": {
        "DEBUG": True,
        "CORS_ORIGINS": ["http://localhost:3000"]
    },
    "database": {
        "ECHO": True
    }
}

PRODUCTION_CONFIG = {
    "api": {
        "DEBUG": False,
        "CORS_ORIGINS": ["https://your-production-domain.com"]
    },
    "database": {
        "POOL_SIZE": 20,
        "MAX_OVERFLOW": 30
    },
    "scraping": {
        "MAX_CONCURRENT_REQUESTS": 16
    }
}

TESTING_CONFIG = {
    "database": {
        "URL": "sqlite:///test.db",
        "ECHO": True
    },
    "api": {
        "DEBUG": True
    }
}

# Create environment-specific config files
def create_env_configs():
    """Create environment-specific configuration files"""
    configs = {
        "development.json": DEVELOPMENT_CONFIG,
        "production.json": PRODUCTION_CONFIG,
        "testing.json": TESTING_CONFIG
    }
    
    config_dir = Path(__file__).parent
    for filename, config in configs.items():
        config_file = config_dir / filename
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

if __name__ == "__main__":
    # Create environment configs if running directly
    create_env_configs()
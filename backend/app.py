# File: /backend/app.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import get_settings
from api.app import api_router
from scraper.controller import ScraperController
from database.manager import DatabaseManager
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path('logs/app.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize components
settings = get_settings()
db = DatabaseManager()
scraper = ScraperController()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    try:
        # Startup
        logger.info("Initializing application...")
        await db.initialize()
        
        yield
        
        # Shutdown
        logger.info("Shutting down application...")
        await scraper.cleanup_jobs()
        await db.cleanup()
    except Exception as e:
        logger.error(f"Error during application lifecycle: {e}")
        raise

# Create FastAPI application
app = FastAPI(
    title="Jewelry Scraper API",
    description="API for scraping and managing jewelry product data",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await db.ping()
        return {
            "status": "healthy",
            "components": {
                "database": "connected",
                "scraper": len(scraper.active_jobs),
                "uptime": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.api.HOST,
        port=settings.api.PORT,
        reload=settings.DEBUG
    )
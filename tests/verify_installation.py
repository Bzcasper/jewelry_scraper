# Create verify_installation.py
import asyncio
async def verify():
    try:
        # Verify core packages
        import scrapy
        import fastapi
        import selenium
        import undetected_chromedriver as uc
        import price_parser
        import prometheus_client
        
        print("✅ All required packages are installed!")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(verify())
import logging
from logging.handlers import SMTPHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()

# Email notifications for critical errors
try:
    smtp_handler = SMTPHandler(
        mailhost=("smtp.gmail.com", 587),
        fromaddr="your-email@gmail.com",
        toaddrs=["developer-email@gmail.com"],
        subject="Scraper Critical Error",
        credentials=("your-email@gmail.com", "your-email-password"),
        secure=()
    )
    smtp_handler.setLevel(logging.CRITICAL)
    logger.addHandler(smtp_handler)
except Exception as e:
    logger.warning(f"Failed to set up SMTPHandler: {e}")

def log_error(message):
    logger.error(message)

def log_critical_error(message):
    logger.critical(message)

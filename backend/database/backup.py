import sqlite3
import shutil
import os
from datetime import datetime
import logging

DB_NAME = "products.db"
BACKUP_DIR = "db_backups"

def backup_database():
    """
    Backup the database to a timestamped file.
    """
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"{DB_NAME}_{timestamp}.bak")
        shutil.copyfile(DB_NAME, backup_file)
        logging.info(f"Database backed up to {backup_file}")
    except Exception as e:
        logging.error(f"Error during database backup: {e}")

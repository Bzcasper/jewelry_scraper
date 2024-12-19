from flask import Flask, request, jsonify
from scraper.ebay_spider import run_ebay_spider
from scraper.amazon_spider import run_amazon_spider
from database.db import initialize_db, add_product, fetch_all_products
from database.backup import backup_database
from logger import log_error, log_critical_error
import logging

app = Flask(__name__)

# Initialize the database
initialize_db()

@app.route('/scrape', methods=['POST'])
def scrape():
    \"\"\"
    Scrapes eBay or Amazon based on the user's query.
    \"\"\"
    data = request.json
    query = data.get("query", "")
    platform = data.get("platform", "ebay")
    max_items = data.get("max_items", 50)

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        # Run the appropriate spider
        if platform == "ebay":
            results = run_ebay_spider(query, max_items)
        elif platform == "amazon":
            results = run_amazon_spider(query, max_items)
        else:
            return jsonify({"error": "Unsupported platform"}), 400

        # Store results in the database
        for product in results:
            add_product(product)

        return jsonify({"message": "Scraping completed", "data": results})
    except Exception as e:
        log_error(f"Error during scraping: {e}")
        return jsonify({"error": "Scraping failed"}), 500

@app.route('/products', methods=['GET'])
def get_products():
    \"\"\"
    Fetch all products from the database.
    \"\"\"
    try:
        products = fetch_all_products()
        return jsonify(products)
    except Exception as e:
        log_error(f"Error fetching products: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500

@app.route('/backup', methods=['GET'])
def trigger_backup():
    \"\"\"
    Trigger a manual database backup.
    \"\"\"
    try:
        backup_database()
        return jsonify({"message": "Database backup completed."})
    except Exception as e:
        log_error(f"Error during backup: {e}")
        return jsonify({"error": "Backup failed"}), 500

if __name__ == "__main__":
    app.run(debug=True) 

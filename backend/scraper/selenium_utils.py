import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36"
]

PROXIES = [
    "http://username:password@proxy_ip:proxy_port",
    "http://proxy_ip:proxy_port"
]

class ProxyManager:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_index = 0

    def get_next_proxy(self):
        """
        Rotate to the next proxy in the list.
        """
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

proxy_manager = ProxyManager(PROXIES)

def setup_driver_with_failover():
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

    proxy = proxy_manager.get_next_proxy()
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    driver = webdriver.Chrome(options=options)
    return driver

def save_html_backup(driver, filename="backup.html"):
    """
    Save the HTML content of the current page to a backup file.
    """
    os.makedirs("backups", exist_ok=True)
    file_path = os.path.join("backups", filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)

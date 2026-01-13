import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ScraperService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def scrape_html(self, url: str, filename: str):
        """
        Scrapes HTML content using Selenium and BeautifulSoup.
        """
        print(f"Scraping HTML from {url}...")
        
        # Configure Selenium options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # In Docker (Linux), we often need to specify the binary
        if os.path.exists("/usr/bin/chromium"):
            chrome_options.binary_location = "/usr/bin/chromium"
        elif os.path.exists("/usr/bin/chromium-browser"):
            chrome_options.binary_location = "/usr/bin/chromium-browser"

        driver = None
        try:
            # Use ChromeService if needed, but default often works if paths are standard
            from selenium.webdriver.chrome.service import Service
            service = None
            if os.path.exists("/usr/bin/chromedriver"):
                service = Service("/usr/bin/chromedriver")
            
            driver = webdriver.Chrome(options=chrome_options, service=service)
            driver.get(url)
            
            # Wait for content to load (adjust selector as needed)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get the page source
            page_source = driver.page_source
            
            # Parse with BeautifulSoup to clean/prettify (optional)
            soup = BeautifulSoup(page_source, "html.parser")
            pretty_html = soup.prettify()
            
            output_path = os.path.join(self.output_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(pretty_html)
                
            print(f"Saved HTML to {output_path}")
            return output_path

        except Exception as e:
            print(f"Error scraping HTML: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def scrape_text(self, url: str, filename: str):
        """
        Scrapes raw text from a URL using requests and BeautifulSoup.
        """
        print(f"Scraping text from {url}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract text
            text_content = soup.get_text(separator="\n", strip=True)
            
            output_path = os.path.join(self.output_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text_content)
                
            print(f"Saved text to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error scraping text: {e}")
            return None

    def fetch_confluence_docs(self):
        """
        Dummy utility for Confluence ingestion.
        """
        print("Fetching Confluence documents (DUMMY)...")
        # Simulate fetching
        dummy_content = "This is a dummy Confluence document content."
        filename = "confluence_dummy.txt"
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(dummy_content)
            
        print(f"Saved dummy Confluence doc to {output_path}")
        return output_path

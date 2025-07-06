import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, timedelta
import logging
import json
import os
import pandas as pd
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SCElectionScraper:
    def __init__(self, headless=True, delay=2, download_dir=None):        
       
        self.url = "https://vrems.scvotes.sc.gov/Candidate/SearchElectionDate"
        self.delay = delay
        self.results = []
        
        # Set up download directory
        if download_dir is None:
            self.download_dir = os.getcwd()
        else:
            self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Master CSV file path
        self.master_csv = os.path.join(self.download_dir, "all_data_SouthCarolina.csv")
        
        # Set up Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Configure download preferences
        chrome_prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", chrome_prefs)
        
        # Initialize the driver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("Chrome WebDriver initialized successfully")
            logger.info(f"Downloads will be saved to: {self.download_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def generate_date_range(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = datetime.now()
        
        if end_date is None:
            # End of current year
            end_date = datetime(start_date.year, 12, 31)
            
        # If we're already past end of year, extend to next year
        if start_date > end_date:
            end_date = datetime(start_date.year + 1, 12, 31)
        
        dates = []
        current_date = start_date
        
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates
    
    def format_date_for_input(self, date_obj):
        return date_obj.strftime("%m/%d/%Y")
    
    def wait_for_download(self, timeout=30):
        """Wait for download to complete and return the downloaded file path"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Look for .csv files in download directory
            csv_files = glob.glob(os.path.join(self.download_dir, "*.csv"))
            
            # Filter out the master CSV file
            new_csv_files = [f for f in csv_files if not f.endswith("all_data_SouthCarolina.csv")]
            
            # Check if any new CSV files exist and are not being downloaded (.crdownload)
            for csv_file in new_csv_files:
                if not csv_file.endswith('.crdownload') and os.path.exists(csv_file):
                    # Wait a bit more to ensure download is complete
                    time.sleep(2)
                    return csv_file
            
            time.sleep(1)
        
        return None
    
    def append_csv_to_master(self, downloaded_csv_path,date):
        """Append the downloaded CSV to the master CSV file"""
        
        try:
            
            new_data = pd.read_csv(downloaded_csv_path)
            logger.info(f"Read {len(new_data)} rows from {downloaded_csv_path}")
            
            # Check if master CSV exists
            if os.path.exists(self.master_csv):
                # Read existing master CSV
                existing_data = pd.read_csv(self.master_csv)
                logger.info(f"Existing master CSV has {len(existing_data)} rows")
                print("error here ")
                # Append new data
                combined_data = pd.concat([existing_data, new_data], ignore_index=True)
            else:
                # Create new master CSV
                combined_data = new_data
                logger.info("Creating new master CSV file")
            
            # Save combined data
            combined_data.to_csv(self.master_csv, index=False)
            logger.info(f"Master CSV updated with {len(combined_data)} total rows")
            
            # Delete the downloaded CSV file
            os.remove(downloaded_csv_path)
            logger.info(f"Deleted temporary file: {downloaded_csv_path}")
            
        except Exception as e:
            logger.error(f"Error processing CSV files: {e}")
            raise
    def delete_csv_simple(self,file_path):
        """
        Simple function to delete a CSV file.
        
        Args:
            file_path (str): Path to the CSV file to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File deleted successfully: {file_path}")
            else:
                print(f"File not found: {file_path}")
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    def search_election_date(self, date_str):
       
        try:
            logger.info(f"Searching for elections on: {date_str}")

            self.driver.get(self.url)
            
            # Wait for the page to load and find the date input
            date_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "ElectionDate"))
            )
            
            # Clear any existing date and enter new date
            date_input.clear()
            date_input.send_keys(date_str)
            curr = self.driver.current_url
            # Find and click the "View Details" button
            view_details_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View Details')]"))
            )
            view_details_btn.click()     
            print("View details clicked") 
            if self.driver.current_url != curr:
                self.robust_click_search_export()
                time.sleep(2)
                print("The current path is ",os.getcwd())
                print("date str is ",date_str)
                date_s = f"{date_str[6:]}-{date_str[0:2]}-{date_str[3:5]}"
                print(date_s)
                downloaded_file = os.path.join(os.getcwd(), f"Candidate Data File for elections on {date_s}.csv")
                print(downloaded_file)
                self.append_csv_to_master(downloaded_file,date_str)

                    
                
                  
            
        except TimeoutException:
            logger.error(f"Timeout while searching for date: {date_str}")
            
    def robust_click_search_export(self):
        # Wait for page to load
        wait = WebDriverWait(self.driver, 10)
        
        # Wait for and click the Search button
        print("Looking for Search button...")
        search_button = wait.until(
            EC.presence_of_element_located((By.ID, "btnSearchByDate"))
        )
        
        # Scroll the button into view
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
        time.sleep(1)
        
        # Try clicking the button, if intercepted use JavaScript click
        try:
            print("Clicking Search button...")
            search_button.click()
        except Exception as e:
            print("Regular click failed, trying JavaScript click...")
            self.driver.execute_script("arguments[0].click();", search_button)
        
        # Wait a moment for search results to load
        time.sleep(3)
        
        # Wait for and click the Export button
        print("Looking for Export button...")
        export_button = wait.until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/Candidate/ExportSearchDateResults')]"))
        )
        
        # Scroll the export button into view
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", export_button)
        time.sleep(1)
        
        # Try clicking the export button, if intercepted use JavaScript click
        try:
            print("Clicking Export button...")
            export_button.click()
        except Exception as e:
            print("Regular click failed, trying JavaScript click...")
            self.driver.execute_script("arguments[0].click();", export_button)
    

        
    
    def run_date_range_search(self, start_date=None, end_date=None, save_results=True):
        try:
            # Generate date range
            dates = self.generate_date_range(start_date, end_date)
            logger.info(f"Searching {len(dates)} dates from {dates[0].strftime('%m/%d/%Y')} to {dates[-1].strftime('%m/%d/%Y')}")
            
            all_results = []
            elections_found = 0
            
            for i, date_obj in enumerate(dates, 1):
                date_str = self.format_date_for_input(date_obj)
                
                logger.info(f"Progress: {i}/{len(dates)} - Checking {date_str}")
                curr = self.driver.current_url
                self.search_election_date(date_str)
                
                print(curr)
                print(self.driver.current_url)
                self.driver.get(curr)
                
            logger.info(f"Date range search completed. Master CSV location: {self.master_csv}")
            
        except Exception as e:
            logger.error(f"Error during date range search: {e}")
            raise
    
   
    
    
    def close(self):
        """Close the webdriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Main function to run the scraper"""
    scraper = None
    try:
        # Initialize scraper
        scraper = SCElectionScraper(headless=False, delay=1)  # Set headless=True for production
        scraper.run_date_range_search()        
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":

    main()
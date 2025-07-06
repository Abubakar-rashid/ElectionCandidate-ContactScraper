from selenium import webdriver # done 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import glob

def setup_chrome_driver():
    """Setup Chrome driver with download preferences"""
    chrome_options = Options()
    # Uncomment the line below to run in headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Set download directory to current working directory
    current_dir = os.getcwd()
    prefs = {
        "download.default_directory": current_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def wait_for_download_and_rename(download_dir, target_filename, timeout=30):
    """Wait for CSV download to complete and rename it"""
    print(f"Waiting for download to complete and renaming to '{target_filename}'...")
    
    # Get initial CSV files
    initial_csv_files = set(glob.glob(os.path.join(download_dir, "*.csv")))
    
    # Wait for new CSV file to appear
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_csv_files = set(glob.glob(os.path.join(download_dir, "*.csv")))
        new_files = current_csv_files - initial_csv_files
        
        if new_files:
            # Get the newest CSV file
            newest_file = max(new_files, key=os.path.getctime)
            
            # Wait a bit more to ensure download is complete
            time.sleep(2)
            
            # Rename the file
            target_path = os.path.join(download_dir, target_filename)
            
            # Remove target file if it already exists
            if os.path.exists(target_path):
                os.remove(target_path)
                print(f"Removed existing file: {target_filename}")
            
            os.rename(newest_file, target_path)
            print(f"File renamed to: {target_filename}")
            return True
        
        time.sleep(1)
    
    print("Timeout waiting for download to complete")
    return False

def scrape_louisiana_candidates():
    """Main function to scrape candidate data from Louisiana voter portal"""
    driver = setup_chrome_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        print("Navigating to Louisiana Voter Portal...")
        driver.get("https://voterportal.sos.la.gov/candidateinquiry")
        
        # Wait for page to load
        time.sleep(3)
        
        print("Step 1: Clicking 'Select All' button...")
        # Find and click the "Select All" button
        select_all_button = wait.until(
            EC.element_to_be_clickable((By.ID, "selectAllCandidates"))
        )
        select_all_button.click()
        print(" Select All clicked successfully")
        
        # Wait a moment for selection to process
        time.sleep(2)
        
        print("Step 2: Clicking 'View Candidates for Selected Race(s)' button...")
        # Find and click the "View Candidates" button - try multiple selectors
        try:
            # First try with the button ID if it exists
            view_candidates_button = wait.until(
                EC.element_to_be_clickable((By.ID, "viewCandidates"))
            )
        except:
            try:
                # Try with the button text
                view_candidates_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View Candidates for Selected Race(s)')]"))
                )
            except:
                # Try with the CSS class combination
                view_candidates_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button#viewCandidates.btn.btn-xs.btn-default"))
                )
        
        view_candidates_button.click()
        print(" View Candidates clicked successfully")
        
        # Wait for the candidate data to load
        time.sleep(5)
        
        print("Step 3: Clicking 'Export to CSV' button...")
        # Find and click the "Export to CSV" button
        export_csv_button = wait.until(
            EC.element_to_be_clickable((By.ID, "exportCSV"))
        )
        export_csv_button.click()
        print(" Export to CSV clicked successfully")
        
        # Wait for download to complete and rename the file
        current_dir = os.getcwd()
        success = wait_for_download_and_rename(current_dir, "all_data_louisiana.csv")
        
        if success:
            print(" Script completed successfully! File saved as 'all_data_louisiana.csv'")
        else:
            # Fallback: check for any CSV files and rename the most recent one
            csv_files = glob.glob(os.path.join(current_dir, "*.csv"))
            if csv_files:
                # Get the most recently modified CSV file
                newest_csv = max(csv_files, key=os.path.getctime)
                target_path = os.path.join(current_dir, "all_data_louisiana.csv")
                
                if os.path.exists(target_path):
                    os.remove(target_path)
                
                os.rename(newest_csv, target_path)
                print(f"Renamed {os.path.basename(newest_csv)} to all_data_louisiana.csv")
            else:
                print(" No CSV files found in current directory")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Take a screenshot for debugging
        driver.save_screenshot("error_screenshot.png")
        print("Screenshot saved as 'error_screenshot.png' for debugging")
        
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    # Install required packages first
    print("Starting Louisiana Voter Portal scraper...")
    print("Make sure you have installed the required packages:")
    print("pip install selenium webdriver-manager")
    print("-" * 50)
    
    scrape_louisiana_candidates()
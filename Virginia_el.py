import time ## done 
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver(download_dir=None):
    """Set up Chrome driver with download preferences"""
    chrome_options = Options()
    
    # Set download directory to current directory if not specified
    if download_dir is None:
        download_dir = os.getcwd()
    
    # Chrome preferences for downloads
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Optional: Run in headless mode (comment out if you want to see the browser)
    chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def download_virginia_elections_csv():
    """Main function to download Virginia 2025 elections CSV"""
    driver = None
    try:
        # Set up the driver
        current_dir = os.getcwd()
        print(f"Setting up download directory: {current_dir}")
        driver = setup_driver(current_dir)
        
        # Navigate to the Virginia elections page
        url = "https://www.elections.virginia.gov/casting-a-ballot/previous-candidate-lists/"
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Look for 2025 elections section
        print("Looking for 2025 election links...")
        
        # Try to find links containing "2025" in the text
        links_2025 = driver.find_elements(By.XPATH, "//a[contains(text(), '2025')]")
        
        if not links_2025:
            print("No 2025 election links found. Checking for any links with '2025' in href...")
            links_2025 = driver.find_elements(By.XPATH, "//a[contains(@href, '2025')]")
        
        if links_2025:
            print(f"Found {len(links_2025)} links containing '2025'")
            for i, link in enumerate(links_2025):
                try:
                    link_text = link.text.encode('ascii', 'ignore').decode('ascii')
                    link_href = link.get_attribute('href')
                    print(f"Link {i+1}: {link_text} - {link_href}")
                except Exception as e:
                    print(f"Link {i+1}: [Text encoding issue] - {link.get_attribute('href')}")
            
            # Click on the first 2025 link (usually the candidate list)
            first_2025_link = links_2025[0]
            try:
                link_text = first_2025_link.text.encode('ascii', 'ignore').decode('ascii')
                print(f"Clicking on: {link_text}")
            except:
                print("Clicking on: [Text encoding issue]")
            first_2025_link.click()
            
            # Wait for the new page to load
            time.sleep(3)
            
            # Look for CSV download links on the new page
            print("Looking for CSV download links...")
            csv_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.csv') or contains(@href, '.xlsx') or contains(text(), 'Download') or contains(text(), 'CSV')]")
            
            if csv_links:
                print(f"Found {len(csv_links)} potential download links")
                for i, link in enumerate(csv_links):
                    try:
                        link_text = link.text.encode('ascii', 'ignore').decode('ascii')
                        link_href = link.get_attribute('href')
                        print(f"Download link {i+1}: {link_text} - {link_href}")
                    except Exception as e:
                        print(f"Download link {i+1}: [Text encoding issue] - {link.get_attribute('href')}")
                
                # Click on the first CSV/download link
                download_link = csv_links[0]
                try:
                    link_text = download_link.text.encode('ascii', 'ignore').decode('ascii')
                    print(f"Clicking download link: {link_text}")
                except:
                    print("Clicking download link: [Text encoding issue]")
                download_link.click()
                
                # Get list of files before download
                files_before = set(os.listdir(current_dir))
                
                # Wait for download to complete
                print("Waiting for download to complete...")
                time.sleep(5)
                
                # Check if file was downloaded by comparing before and after
                files_after = set(os.listdir(current_dir))
                new_files = files_after - files_before
                
                # Filter for CSV/Excel files
                downloaded_files = [f for f in new_files if f.endswith(('.csv', '.xlsx'))]
                
                if downloaded_files:
                    # Get the downloaded file (should be only one)
                    latest_file = downloaded_files[0]
                    print(f"New file detected: {latest_file}")
                    
                    # Handle different file types
                    if latest_file.endswith('.xlsx'):
                        print(f"Downloaded Excel file: {latest_file}")
                        # Convert Excel to CSV
                        if convert_xlsx_to_csv(latest_file, "all_data_virginia.csv"):
                            # Delete the original Excel file after successful conversion
                            os.remove(latest_file)
                            print(f" Deleted original Excel file: {latest_file}")
                            print(f"Successfully created: all_data_virginia.csv")
                            return True
                        else:
                            print(" Failed to convert Excel to CSV")
                            return False
                    else:
                        # File is already CSV, just rename it
                        new_name = "all_data_virginia.csv"
                        if latest_file != new_name:
                            os.rename(latest_file, new_name)
                            print(f" File renamed from '{latest_file}' to '{new_name}'")
                        else:
                            print(f" File already named correctly: {new_name}")
                        
                        print(f" Successfully downloaded: {new_name}")
                        return True
                else:
                    print(" No files found in download directory")
                    return False
            else:
                print(" No CSV download links found on the page")
                
                # Try to find any downloadable files
                all_links = driver.find_elements(By.TAG_NAME, "a")
                downloadable_links = []
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', '.pdf']):
                        downloadable_links.append((link.text.strip(), href))
                
                if downloadable_links:
                    print("Found other downloadable files:")
                    for text, href in downloadable_links:
                        try:
                            safe_text = text.encode('ascii', 'ignore').decode('ascii')
                            print(f"  - {safe_text}: {href}")
                        except:
                            print(f"  - [Text encoding issue]: {href}")
                
                return False
        else:
            print("No 2025 election links found on the page")
            
            # Print all available links for debugging
            all_links = driver.find_elements(By.TAG_NAME, "a")
            print(f"\nAll links found on page ({len(all_links)} total):")
            for i, link in enumerate(all_links[:10]):  # Show first 10 links
                try:
                    text = link.text.strip().encode('ascii', 'ignore').decode('ascii')
                    href = link.get_attribute('href')
                    if text and href:
                        print(f"  {i+1}. {text} - {href}")
                except:
                    href = link.get_attribute('href')
                    if href:
                        print(f"  {i+1}. [Text encoding issue] - {href}")
            
            return False
            
    except TimeoutException:
        print(" Timeout waiting for page elements")
        return False
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False
    finally:
        if driver:
            driver.quit()

def convert_xlsx_to_csv(xlsx_file, csv_file):
    """Convert Excel file to CSV (requires pandas and openpyxl)"""
    try:
        import pandas as pd
        df = pd.read_excel(xlsx_file)
        df.to_csv(csv_file, index=False)
        print(f"Converted {xlsx_file} to {csv_file}")
        return True
    except ImportError:
        print(" pandas and openpyxl required for Excel to CSV conversion")
        print("Install with: pip install pandas openpyxl")
        return False
    except Exception as e:
        print(f" Error converting file: {str(e)}")
        return False

if __name__ == "__main__":
    print(" Starting Virginia Elections CSV Downloader...")
    print("=" * 50)
    
    success = download_virginia_elections_csv()
    
    if success:
        print("\n Script completed successfully!")
        print("Final result: all_data_virginia.csv")
    else:
        print("\n Script failed to download the file")
        print("You may need to manually navigate to the website and download the file")
    
    print("\n" + "=" * 50)
    print("Script finished.")
from selenium import webdriver #done
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
import os 
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv

def scrape_candidate_links():
    """
    Scrapes candidate profile links from Georgia Campaign Finance System
    Handles pagination to get all candidates across multiple pages
    """
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Remove this line to see the browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Initialize the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to the website
        url = "https://efile.ethics.ga.gov/index.html#/explore/candidate"
        print(f"Opening URL: {url}")
        driver.get(url)
        
        # Wait for the page to load
        print("Waiting for page to load...")
        time.sleep(30)
        
        # Wait for the candidate table to be present
        wait = WebDriverWait(driver, 20)
        
        # Look for candidate name links specifically across all pages
        print("Looking for candidate profile links across all pages...")
        
        all_candidate_data = []
        page_number = 1
        
        while True:
            print(f"\n--- Processing Page {page_number} ---")
            
            # Wait for the current page to load
            time.sleep(3)
            
            # Get candidates from current page
            page_candidate_data = []
            
            try:
                # Wait for the candidate table to load
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[md-body], table")))
                
                # Find all links that contain exploreDetails in href on current page
                candidate_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'exploreDetails')]")
                print(f"Found {len(candidate_links)} candidate profile links on page {page_number}")
                
                for link in candidate_links:
                    try:
                        href = link.get_attribute('href')
                        name = link.text.strip()
                        
                        # Get additional context (office) if available
                        # Look for the office in the same row
                        parent_row = link.find_element(By.XPATH, "./ancestor::tr")
                        office_cells = parent_row.find_elements(By.TAG_NAME, "td")
                        office = ""
                        if len(office_cells) > 1:
                            office = office_cells[1].text.strip()
                        
                        if href and name:
                            candidate_info = {
                                'name': name,
                                'href': href,
                                'office': office,
                                'page': page_number
                            }
                            page_candidate_data.append(candidate_info)
                            
                    except Exception as e:
                        print(f"Error processing link on page {page_number}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
            
            # Add current page data to all data
            all_candidate_data.extend(page_candidate_data)
            print(f"Collected {len(page_candidate_data)} candidates from page {page_number}")
            print(f"Total candidates so far: {len(all_candidate_data)}")
            
            # Try to find and click the "Next" button
            next_button_found = False
            try:
                # Look for next button with various possible selectors
                next_selectors = [
                    "//button[contains(text(), 'Next')]",
                    "//button[contains(@aria-label, 'Next')]",
                    "//button[contains(@ng-click, 'next')]",
                    "//button[contains(@class, 'next')]",
                    "//md-icon[text()='navigate_next']/parent::button",
                    "//button[@ng-click='pagination.next()']",
                    "//button[contains(@ng-disabled, '!pagination.hasNext()')]"
                ]
                
                for selector in next_selectors:
                    try:
                        next_buttons = driver.find_elements(By.XPATH, selector)
                        for next_button in next_buttons:
                            # Check if button is enabled (not disabled)
                            if next_button.is_enabled():
                                disabled_attr = next_button.get_attribute('disabled')
                                ng_disabled = next_button.get_attribute('ng-disabled')
                                
                                # Check if button is actually clickable
                                if not disabled_attr and not next_button.get_attribute('aria-disabled'):
                                    print(f"Found Next button with selector: {selector}")
                                    
                                    # Scroll to button and click
                                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                    time.sleep(1)
                                    
                                    # Try clicking with JavaScript if regular click fails
                                    try:
                                        next_button.click()
                                    except:
                                        driver.execute_script("arguments[0].click();", next_button)
                                    
                                    next_button_found = True
                                    page_number += 1
                                    print(f"Clicked Next button, moving to page {page_number}")
                                    time.sleep(3)  # Wait for page to load
                                    break
                                    
                        if next_button_found:
                            break
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Error looking for Next button: {e}")
            
            # If no next button found or clickable, we've reached the end
            if not next_button_found:
                print(f"No more pages found. Finished scraping at page {page_number - 1}")
                break
                
            # Safety check to avoid infinite loops
            if page_number > 50:  # Adjust this limit as needed
                print("Reached maximum page limit (50). Stopping to avoid infinite loop.")
                break
        
        candidate_data = all_candidate_data
        
        # Remove duplicates and clean up
        candidate_links = list(set(candidate_links))
        
        # Print results with candidate names and offices
        print(f"\nFound {len(candidate_data)} candidates with profile links:")
        print("-" * 100)
        print(f"{'#':<3} {'Name':<25} {'Office':<25} {'Profile Link'}")
        print("-" * 100)
        
        for i, candidate in enumerate(candidate_data, 1):
            name = candidate['name'][:24] if len(candidate['name']) > 24 else candidate['name']
            office = candidate['office'][:24] if len(candidate['office']) > 24 else candidate['office']
            print(f"{i:<3} {name:<25} {office:<25} {candidate['href']}")
        
        # Also print just the links for easy copying
        print(f"\nProfile Links Only:")
        print("-" * 80)
        for i, link in enumerate(candidate_links, 1):
            print(f"{i:3d}. {link}")
        
        return candidate_data
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
        # Try to get page source for debugging
        try:
            print("\nPage title:", driver.title)
            print("Current URL:", driver.current_url)
            
            # Save page source for debugging
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Page source saved to debug_page_source.html")
            
        except:
            pass
            
        return []
        
    finally:
        driver.quit()

def safe_extract_field(driver, field_name, xpath_selector, max_retries=3, wait_time=1):
    """
    Safely extract a field value with retries and proper error handling
    
    Args:
        driver: Selenium WebDriver instance
        field_name: Name of the field being extracted (for logging)
        xpath_selector: XPath selector for the field
        max_retries: Maximum number of retry attempts
        wait_time: Time to wait between retries
    
    Returns:
        str: Field value or "N/A" if not found
    """
    for attempt in range(max_retries):
        try:
            element = driver.find_element(By.XPATH, xpath_selector)
            value = element.text.strip()
            
            # Handle special formatting for address fields
            if 'Address' in field_name and '\n' in value:
                value = value.replace('\n', ', ')
            
            return value if value else "N/A"
            
        except NoSuchElementException:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries}: {field_name} not found, retrying...")
                time.sleep(wait_time)
            else:
                print(f"  {field_name}: Field not found after {max_retries} attempts")
                return "N/A"
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries}: Error extracting {field_name}: {e}")
                time.sleep(wait_time)
            else:
                print(f"  {field_name}: Error after {max_retries} attempts: {e}")
                return "N/A"
    
    return "N/A"

def scrape_candidate_data(input_csv='candidate_data.csv', output_csv='all_data_georgia.csv'):
    """
    Scrape candidate data from individual candidate pages with improved error handling
    """
    # Read input CSV
    df = pd.read_csv(input_csv)

    # Check if output CSV exists and load existing data
    existing_data = []
    existing_names = set()
    
    if os.path.exists(output_csv):
        try:
            existing_df = pd.read_csv(output_csv)
            existing_data = existing_df.to_dict('records')
            # Create a set of existing names for quick lookup
            existing_names = set(existing_df['Name'].str.strip().str.lower())
            print(f"Found {len(existing_data)} existing records in {output_csv}")
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
            existing_data = []
            existing_names = set()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    new_data = []
    skipped_count = 0
    failed_count = 0

    # Define the fields to extract with their XPath selectors
    field_selectors = {
        'Status': "//div[contains(text(), 'Status')]/following-sibling::div",
        'Candidate Email': "//div[contains(text(), 'Candidate Email')]/following-sibling::div",
        'Candidate Address': "//div[contains(text(), 'Candidate Address')]/following-sibling::div",
        'Treasurer': "//div[contains(text(), 'Treasurer')]/following-sibling::div",
        'Chairperson': "//div[contains(text(), 'Chairperson')]/following-sibling::div",
        'Committee Name': "//div[contains(text(), 'Committee Name')]/following-sibling::div",
        'Committee Email': "//div[contains(text(), 'Committee Email')]/following-sibling::div",
        'Election(s)': "//div[contains(text(), 'Election(s)')]/following-sibling::div",
        'Date Registered': "//div[contains(text(), 'Date Registered')]/following-sibling::div"
    }

    for index, row in df.iterrows():
        url = row['href']
        name = row['name']
        office = row['office']
        
        # Check if candidate already exists (case-insensitive comparison)
        if name.strip().lower() in existing_names:
            print(f"Skipping {name} - already exists in output file")
            skipped_count += 1
            continue
            
        print(f"Scraping {name} - {url}")
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # Initialize data dictionary with basic info
            data = {
                'Name': name,
                'Office': office
            }
            
            # Extract each field safely
            print(f"  Extracting data for {name}...")
            for field_name, xpath_selector in field_selectors.items():
                field_value = safe_extract_field(driver, field_name, xpath_selector)
                data[field_name] = field_value
            
            print(f"  Successfully extracted data for {name}")
            print(f"  Data: {data}")
            new_data.append(data)
            
            # Add to existing names set to avoid duplicates within the same run
            existing_names.add(name.strip().lower())
            
        except Exception as e:
            print(f"  Critical error processing {name}: {e}")
            failed_count += 1
            continue
            
        time.sleep(1)  # Rate limiting

    driver.quit()

    # Combine existing data with new data
    all_data = existing_data + new_data

    # Write all data to output CSV
    if all_data:
        # Get all possible fieldnames from existing and new data
        all_fieldnames = set()
        for record in all_data:
            all_fieldnames.update(record.keys())
        
        fieldnames = list(all_fieldnames)
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)

    # Delete the input CSV file after successful scraping
    try:
        os.remove(input_csv)
        print(f"Input file {input_csv} has been deleted successfully")
    except OSError as e:
        print(f"Error deleting input file {input_csv}: {e}")

    print(f"\nScraping Summary:")
    print(f"- Added {len(new_data)} new records")
    print(f"- Skipped {skipped_count} duplicates")
    print(f"- Failed to process {failed_count} candidates")
    print(f"- Total records in {output_csv}: {len(all_data)}")

def main():
    """
    Main function to run the scraper
    """
    print("Georgia Campaign Finance System - Candidate Link Scraper")
    print("=" * 60)
    
    links = scrape_candidate_links()
    
    if links:
        import csv

        # Save detailed candidate data to CSV (including 'page' info)
        with open("candidate_data.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ['name', 'office', 'href', 'page']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for candidate in links:
                writer.writerow(candidate)
        
        # Save just the profile links to a text file
        candidate_links_only = list({c['href'] for c in links})  # Extract unique hrefs
        with open("candidate_links.txt", "w", encoding="utf-8") as f:
            for link in candidate_links_only:
                f.write(link + "\n")
        
        print(f"\nScraping completed! Found {len(links)} candidates.")
        print("Detailed data saved to 'candidate_data.csv'")
        print("Links only saved to 'candidate_links.txt'")
    else:
        print("\nNo candidate links found. Check the debug output above.")
        
if __name__ == "__main__":
    main()
    time.sleep(2)
    scrape_candidate_data()
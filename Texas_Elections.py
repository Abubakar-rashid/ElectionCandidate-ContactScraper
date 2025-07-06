from selenium import webdriver # done 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import csv
import pandas as pd
from datetime import datetime
import os
import re

options = webdriver.ChromeOptions()
# Uncomment the next line if you want to run in headless mode
options.add_argument('--headless')
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
options.add_argument("--start-maximized")

def get_dropdown_options(driver, dropdown_id):
    """Get all valid options from a dropdown"""
    try:
        dropdown = driver.find_element(By.ID, dropdown_id)
        select_obj = Select(dropdown)
        options = select_obj.options
        valid_options = []
        
        for option in options:
            value = option.get_attribute("value")
            text = option.text
            if value and value != "" and value != "0" and "Select" not in text:
                valid_options.append({"value": value, "text": text})
        
        return valid_options
    except Exception as e:
        print(f"Error getting dropdown options: {e}")
        return []

def clean_text(text):
    """Clean and normalize text data"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove common prefixes
    text = re.sub(r'^E-mail:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Phone:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Address:\s*', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def extract_contact_info(text):
    """Extract email and phone from text"""
    email = ""
    phone = ""
    
    # Extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        email = email_match.group()
    
    # Extract phone number
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',        # 123.456.7890
        r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # +1 (123) 456-7890
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = phone_match.group()
            break
    
    return email, phone

def scrape_candidate_info(driver, wait):
    """Scrape all candidate information from the current page"""
    candidates = []
    
    try:
        # Wait for the candidate information to load
        time.sleep(3)
        
        # Look for candidate containers - trying multiple possible selectors
        candidate_selectors = [
            "div.row.mb-3",  # Based on the HTML structure seen
            "div[class*='row'][class*='mb']",
            "div.candidate-info",
            ".container-fluid .row"
        ]
        
        candidate_elements = []
        for selector in candidate_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} elements using selector: {selector}")
                    candidate_elements = elements
                    break
            except:
                continue
        
        if not candidate_elements:
            # Fallback: get all content and try to parse
            print("Using fallback method to find candidate information...")
            page_source = driver.page_source
            
            # Try to find candidate information in the page source
            if "REYNA ANDERSON" in page_source or "CANDIDATE" in page_source:
                # Extract visible text from the page
                body = driver.find_element(By.TAG_NAME, "body")
                all_text = body.text
                
                # Parse the text to extract candidate information
                lines = all_text.split('\n')
                current_candidate = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for candidate names (usually all caps or followed by position)
                    if any(keyword in line.upper() for keyword in ['DISTRICT', 'REPRESENTATIVE', 'SENATOR', 'JUDGE']):
                        if current_candidate:
                            candidates.append(current_candidate)
                            current_candidate = {}
                        current_candidate['position'] = line
                    elif line.isupper() and len(line.split()) >= 2 and not any(skip in line for skip in ['PARTY:', 'STATUS:', 'OCCUPATION:']):
                        current_candidate['name'] = line
                    elif line.startswith('PARTY:'):
                        current_candidate['party'] = line.replace('PARTY:', '').strip()
                    elif line.startswith('STATUS:'):
                        current_candidate['status'] = line.replace('STATUS:', '').strip()
                    elif line.startswith('OCCUPATION:'):
                        current_candidate['occupation'] = line.replace('OCCUPATION:', '').strip()
                    elif '@' in line and '.' in line:
                        current_candidate['email'] = clean_text(line)
                    elif line.upper().startswith('HOUSTON') or line.upper().startswith('DALLAS') or 'TX' in line.upper():
                        current_candidate['address'] = line
                    elif line.startswith('FILING DATE:'):
                        current_candidate['filing_date'] = line.replace('FILING DATE:', '').strip()
                    elif line.startswith('INCUMBENT:'):
                        current_candidate['incumbent'] = line.replace('INCUMBENT:', '').strip()
                
                # Add the last candidate if exists
                if current_candidate:
                    candidates.append(current_candidate)
        
        else:
            # Process each candidate element
            for i, element in enumerate(candidate_elements):
                try:
                    candidate_info = {}
                    
                    # Get all text from this element
                    element_text = element.text.strip()
                    if not element_text or len(element_text) < 10:
                        continue
                    
                    print(f"Processing candidate element {i+1}:")
                    print(f"Text content: {element_text[:200]}...")
                    
                    # Parse the element text
                    lines = element_text.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Extract different types of information
                        if any(keyword in line.upper() for keyword in ['DISTRICT', 'REPRESENTATIVE', 'SENATOR', 'JUDGE', 'TERM']):
                            candidate_info['position'] = line
                        elif line.isupper() and len(line.split()) >= 2 and not any(skip in line for skip in ['PARTY:', 'STATUS:', 'OCCUPATION:']):
                            if 'name' not in candidate_info:
                                candidate_info['name'] = line
                        elif 'PARTY:' in line.upper():
                            candidate_info['party'] = line.split(':', 1)[1].strip() if ':' in line else line
                        elif 'STATUS:' in line.upper():
                            candidate_info['status'] = line.split(':', 1)[1].strip() if ':' in line else line
                        elif 'OCCUPATION:' in line.upper():
                            candidate_info['occupation'] = line.split(':', 1)[1].strip() if ':' in line else line
                        elif 'INCUMBENT:' in line.upper():
                            candidate_info['incumbent'] = line.split(':', 1)[1].strip() if ':' in line else line
                        elif 'FILING DATE:' in line.upper():
                            candidate_info['filing_date'] = line.split(':', 1)[1].strip() if ':' in line else line
                        elif '@' in line and '.' in line:
                            candidate_info['email'] = clean_text(line)
                        elif any(state in line.upper() for state in ['TX', 'TEXAS']) and any(char.isdigit() for char in line):
                            if 'address' not in candidate_info:
                                candidate_info['address'] = line
                    
                    # Only add if we have meaningful information
                    if len(candidate_info) >= 2:
                        candidates.append(candidate_info)
                    
                except Exception as e:
                    print(f"Error processing candidate element {i}: {e}")
                    continue
        
        print(f"Successfully scraped {len(candidates)} candidates")
        return candidates
        
    except Exception as e:
        print(f"Error scraping candidate information: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_candidates_data(candidates, election_name, year):
    """Process candidate data and convert to desired format"""
    if not candidates:
        print("No candidate data to process")
        return []
    
    processed_candidates = []
    
    for candidate in candidates:
        # Create processed candidate record with desired format
        processed_candidate = {
            'First Name': '',
            'Last Name': '',
            'Email Address': '',
            'Phone Number': '',
            'Political Title': '',
            'State': 'TX',  # Since this is Texas elections
            'Address': '',
            'Party Affiliation': ''
        }
        
        # Extract name components
        full_name = candidate.get('name', '').strip()
        if full_name:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                processed_candidate['First Name'] = name_parts[0]
                processed_candidate['Last Name'] = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                processed_candidate['Last Name'] = name_parts[0]
        
        # Extract email and phone from various text fields
        email_sources = [
            candidate.get('email', ''),
            candidate.get('address', ''),
            str(candidate)  # Sometimes contact info is mixed in
        ]
        
        phone_number = ''
        email_address = ''
        
        for source in email_sources:
            if source:
                extracted_email, extracted_phone = extract_contact_info(str(source))
                if extracted_email and not email_address:
                    email_address = extracted_email
                if extracted_phone and not phone_number:
                    phone_number = extracted_phone
        
        processed_candidate['Email Address'] = email_address
        processed_candidate['Phone Number'] = phone_number
        
        # Political title (position)
        processed_candidate['Political Title'] = candidate.get('position', '')
        
        # Address (clean it up)
        address = candidate.get('address', '')
        if address:
            # Remove email and phone from address if they got mixed in
            address = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', address)
            address = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', address)
            processed_candidate['Address'] = clean_text(address)
        
        # Party affiliation
        processed_candidate['Party Affiliation'] = candidate.get('party', '')
        
        # Clean all fields
        for key in processed_candidate:
            processed_candidate[key] = clean_text(str(processed_candidate[key]))
        
        processed_candidates.append(processed_candidate)
    
    return processed_candidates

def save_candidates_data(candidates, election_name, year):
    """Save candidate data to all_data_texas.csv, avoiding duplicates"""
    if not candidates:
        print("No candidate data to save")
        return
    
    # Process candidates to desired format
    processed_candidates = process_candidates_data(candidates, election_name, year)
    
    if not processed_candidates:
        print("No processed candidate data to save")
        return
    
    csv_filename = "all_data_texas.csv"
    
    # Define the desired column order
    fieldnames = [
        'First Name',
        'Last Name',
        'Email Address',
        'Phone Number',
        'Political Title',
        'State',
        'Address',
        'Party Affiliation'
    ]
    
    # Check if file exists and load existing data
    existing_df = pd.DataFrame()
    file_exists = os.path.exists(csv_filename)
    
    if file_exists:
        try:
            existing_df = pd.read_csv(csv_filename)
            print(f"Found existing CSV with {len(existing_df)} records")
        except Exception as e:
            print(f"Error reading existing CSV: {e}")
            existing_df = pd.DataFrame()
    else:
        print("No existing CSV found, will create new file")
    
    # Convert processed candidates to DataFrame
    new_df = pd.DataFrame(processed_candidates)
    
    # Ensure all columns exist in both dataframes
    for col in fieldnames:
        if col not in existing_df.columns:
            existing_df[col] = ''
        if col not in new_df.columns:
            new_df[col] = ''
    
    # Reorder columns
    existing_df = existing_df[fieldnames]
    new_df = new_df[fieldnames]
    
    # Combine existing and new data
    if not existing_df.empty:
        all_data = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
        print(f"Total records before deduplication: {len(all_data)}")
    else:
        all_data = new_df
        print(f"No existing data, using only new records: {len(all_data)}")
    
    # Remove duplicates based on key fields
    duplicate_check_columns = ['First Name', 'Last Name', 'Email Address', 'Political Title']
    
    before_dedup = len(all_data)
    all_data = all_data.drop_duplicates(subset=duplicate_check_columns, keep='first')
    after_dedup = len(all_data)
    
    duplicates_removed = before_dedup - after_dedup
    new_records_added = len(new_df) - duplicates_removed
    
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"New records added: {new_records_added}")
    print(f"Final record count: {after_dedup}")
    
    # Save to CSV
    all_data.to_csv(csv_filename, index=False, encoding='utf-8')
    
    print(f"Successfully saved data to: {csv_filename}")
    print(f"File size: {os.path.getsize(csv_filename) / (1024*1024):.2f} MB")
    
    # Display summary of new candidates only
    if new_records_added > 0:
        print(f"\nNew Candidates Added for {election_name}:")
        print("-" * 50)
        
        # Get the newly added candidates (last N records)
        recent_candidates = all_data.tail(new_records_added)
        
        for i, (_, candidate) in enumerate(recent_candidates.iterrows(), 1):
            print(f"{i}. {candidate['First Name']} {candidate['Last Name']}")
            print(f"   Political Title: {candidate['Political Title']}")
            print(f"   Party: {candidate['Party Affiliation']}")
            if candidate['Email Address']:
                print(f"   Email: {candidate['Email Address']}")
            if candidate['Phone Number']:
                print(f"   Phone: {candidate['Phone Number']}")
            print()
    
    # Display basic statistics
    print(f"\nData Summary:")
    print(f"  - Total Records: {len(all_data)}")
    print(f"  - Records with Email: {len(all_data[all_data['Email Address'] != ''])}")
    print(f"  - Records with Phone: {len(all_data[all_data['Phone Number'] != ''])}")
    print(f"  - Unique Political Titles: {all_data['Political Title'].nunique()}")
    print(f"  - Unique Parties: {all_data['Party Affiliation'].nunique()}")

def automate_texas_elections():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://candidate.texas-election.com/Elections/getQualifiedCandidatesInfo.do")
        print("Navigated to Texas Elections page")
        
        wait = WebDriverWait(driver, 20)
        time.sleep(5)
        
        # Step 1: Select the latest year
        print("Step 1: Selecting the latest year...")
        year_dropdown = wait.until(EC.presence_of_element_located((By.ID, "nbElecYear")))
        wait.until(EC.element_to_be_clickable(year_dropdown))
        
        select_year = Select(year_dropdown)
        all_year_options = select_year.options
        available_years = []
        
        for option in all_year_options:
            value = option.get_attribute("value")
            if value and value != "" and value != "0":
                available_years.append(value)
        
        if available_years:
            latest_year = max(available_years)
            print(f"Selecting latest year: {latest_year}")
            select_year.select_by_value(latest_year)
            time.sleep(3)  # Wait for election dropdown to populate
            
            # Step 2: Get all election options for the latest year
            print("Step 2: Getting all election options...")
            time.sleep(2)  # Additional wait for dropdown to populate
            available_elections = get_dropdown_options(driver, "idElection")
            
            print(f"Found {len(available_elections)} elections:")
            for election in available_elections:
                print(f"  - {election['text']}")
            
            # Step 3: Process each election
            for election_index, election in enumerate(available_elections):
                print(f"\n--- Processing Election {election_index + 1}/{len(available_elections)} ---")
                print(f"Election: {election['text']}")
                
                try:
                    # Select the election
                    election_dropdown = driver.find_element(By.ID, "idElection")
                    select_election = Select(election_dropdown)
                    select_election.select_by_value(election['value'])
                    print(f"Selected election: {election['text']}")
                    
                    time.sleep(2)  # Brief wait
                    
                    # Click "Qualified Candidates Information" button
                    print("Clicking Qualified Candidates Information button...")
                    try:
                        # Try multiple selectors for the button
                        info_button = None
                        selectors = [
                            (By.CSS_SELECTOR, "button.btn.btn-primary[onclick*='submitForm']"),
                            (By.XPATH, "//button[contains(@class, 'btn btn-primary') and contains(@onclick, 'submitForm')]"),
                            (By.XPATH, "//button[contains(text(), 'Qualified Candidates Information')]"),
                            (By.CSS_SELECTOR, "button.btn.btn-primary"),
                            (By.XPATH, "//input[@value='Qualified Candidates Information']")
                        ]
                        
                        for selector_type, selector in selectors:
                            try:
                                info_button = wait.until(EC.element_to_be_clickable((selector_type, selector)))
                                print(f"Found button using selector: {selector}")
                                break
                            except:
                                continue
                        
                        if info_button:
                            info_button.click()
                            print("Clicked Qualified Candidates Information button")
                            time.sleep(5)  # Wait to see results
                            
                            # Scrape candidate information
                            print("Scraping candidate information...")
                            candidates = scrape_candidate_info(driver, wait)
                            
                            if candidates:
                                save_candidates_data(candidates, election['text'], latest_year)
                            else:
                                print("No candidate information found to scrape")
                            
                            time.sleep(2)  # Brief pause before next election
                        else:
                            print("Could not find the Qualified Candidates Information button")
                        
                    except Exception as e:
                        print(f"Error clicking info button: {e}")
                    
                except Exception as e:
                    print(f"Error processing election {election['text']}: {e}")
                    continue
        
        print(f"\n=== COMPLETED ===")
        print("Processed all elections for the latest year")
        
        # Keep browser open to see final results
        print("Keeping browser open for 10 seconds to view final results...")
        
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("Browser closed")


if __name__ == "__main__":
    print("Starting Texas Elections Data Processing...")
    print("=" * 50)
    automate_texas_elections()
    print("Texas elections processing completed!")
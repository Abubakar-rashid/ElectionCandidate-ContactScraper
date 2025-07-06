from selenium import webdriver # done
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import pandas as pd
import PyPDF2
import re
from urllib.parse import urljoin
import requests

def setup_chrome_driver():
    """Setup Chrome driver with download preferences"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
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

def download_pdf_directly(driver, pdf_url):
    """Download PDF directly using requests"""
    try:
        response = requests.get(pdf_url)
        if response.status_code == 200:
            filename = "shawnee_candidates.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"PDF downloaded successfully as {filename}")
            return filename
        else:
            print(f"Failed to download PDF. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def parse_candidate_data(text):
    """Parse candidate information from PDF text"""
    candidates = []
    
    # Split text into sections based on candidate entries
    sections = re.split(r'Candidate\s+Ballot\s+City\s+Date\s+Filed\s+Filing\s+Method\s+Address\s+Info\s+Contact\s+Info\s+Filed\s+Documents', text)
    
    for section in sections[1:]:  # Skip the first section (header info)
        lines = section.strip().split('\n')
        
        # Find the office/position title (usually appears before candidate data)
        office = ""
        for i, line in enumerate(lines):
            if "School Board Member" in line or "Mayor" in line or "City Council" in line or "Drainage" in line or "Improvement" in line:
                office = line.strip()
                break
        
        # Extract candidate information
        candidate_lines = []
        current_candidate = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts a new candidate entry
            # Look for patterns like "Name City Date"
            candidate_match = re.match(r'^([A-Za-z\s\.\(\)"\-]+?)\s+([A-Za-z\s]+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(Fee|Petition)', line)
            
            if candidate_match:
                # Save previous candidate if exists
                if current_candidate:
                    candidates.append(current_candidate)
                
                # Start new candidate
                current_candidate = {
                    'name': candidate_match.group(1).strip(),
                    'city': candidate_match.group(2).strip(),
                    'date_filed': candidate_match.group(3).strip(),
                    'filing_method': candidate_match.group(4).strip(),
                    'office': office,
                    'address': '',
                    'phone': '',
                    'email': '',
                    'documents': ''
                }
                
                # Extract remaining info from the same line
                remaining_text = line[candidate_match.end():].strip()
                if remaining_text:
                    current_candidate['address'] = remaining_text
                    
            elif current_candidate:
                # Continue processing current candidate's information
                # Look for phone numbers
                phone_match = re.search(r'\((\d{3})\)(\d{3})-(\d{4})', line)
                if phone_match:
                    current_candidate['phone'] = f"({phone_match.group(1)}){phone_match.group(2)}-{phone_match.group(3)}"
                
                # Look for email addresses
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                if email_match:
                    current_candidate['email'] = email_match.group()
                
                # Look for addresses (lines with street numbers/names)
                if re.search(r'\d+\s+[A-Za-z\s]+(St|Ave|Rd|Dr|Ln|Ter|Pl|Ct|Cir)', line):
                    if not current_candidate['address']:
                        current_candidate['address'] = line
                    elif line not in current_candidate['address']:
                        current_candidate['address'] += f", {line}"
                
                # Look for documents
                if "Affidavit" in line or "Candidate Declaration" in line or "Statement" in line:
                    if current_candidate['documents']:
                        current_candidate['documents'] += f"; {line}"
                    else:
                        current_candidate['documents'] = line
        
        # Add the last candidate
        if current_candidate:
            candidates.append(current_candidate)
    
    return candidates

def clean_candidate_data(candidates):
    """Clean and standardize candidate data"""
    cleaned_candidates = []
    
    for candidate in candidates:
        # Clean name - remove extra quotes and parentheses
        name = re.sub(r'["\(\)]+', '', candidate.get('name', '')).strip()
        name = re.sub(r'\s+', ' ', name)  # Remove extra spaces
        
        # Skip if name is too short or looks invalid
        if len(name) < 2 or name.lower() in ['candidate', 'school', 'city', 'drainage']:
            continue
            
        cleaned_candidate = {
            'name': name,
            'office': candidate.get('office', '').strip(),
            'city': candidate.get('city', '').strip(),
            'date_filed': candidate.get('date_filed', '').strip(),
            'filing_method': candidate.get('filing_method', '').strip(),
            'address': candidate.get('address', '').strip(),
            'phone': candidate.get('phone', '').strip(),
            'email': candidate.get('email', '').strip(),
            'documents': candidate.get('documents', '').strip()
        }
        
        cleaned_candidates.append(cleaned_candidate)
    
    return cleaned_candidates

def save_to_csv(candidates, filename="all_data_shawnee.csv"):
    """Save candidate data to CSV file"""
    try:
        df = pd.DataFrame(candidates)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        print(f"Total candidates extracted: {len(candidates)}")
        return True
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False

def automate_shawnee():
    """Main function to automate the process"""
    driver = setup_chrome_driver()
    
    try:
        wait = WebDriverWait(driver, 10)
        url = "https://candidatefiling.us/Info/?st=KS&jx=E5422&ex=C9D36"
        driver.get(url)
        
        # Wait for page to load
        time.sleep(2)
        
        # Find and get the PDF URL
        pdf_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[@target='_pdf']"))
        )
        
        pdf_url = pdf_link.get_attribute('href')
        print(f"Found PDF URL: {pdf_url}")
        
        # Download PDF directly
        pdf_filename = download_pdf_directly(driver, pdf_url)
        
        if pdf_filename and os.path.exists(pdf_filename):
            print("PDF downloaded successfully!")
            
            # Extract text from PDF
            print("Extracting text from PDF...")
            pdf_text = extract_text_from_pdf(pdf_filename)
            
            if pdf_text:
                print("Text extracted successfully!")
                
                # Parse candidate data
                print("Parsing candidate data...")
                candidates = parse_candidate_data(pdf_text)
                
                # Clean the data
                print("Cleaning candidate data...")
                cleaned_candidates = clean_candidate_data(candidates)
                
                # Save to CSV
                print("Saving data to CSV...")
                if save_to_csv(cleaned_candidates):
                    print("Process completed successfully!")
                    
                    # Display sample data
                    if cleaned_candidates:
                        print("\nSample of extracted data:")
                        df = pd.DataFrame(cleaned_candidates)
                        print(df.head())
                else:
                    print("Failed to save data to CSV")
            else:
                print("Failed to extract text from PDF")
        else:
            print("Failed to download PDF")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()
import pandas as pd

def modify_csv(input_file, output_file):
    # Read the CSV
    df = pd.read_csv(input_file)

    # Modify the name and city columns
    def update_name_city(row):
        city_parts = str(row['city']).split()
        if city_parts:
            first_word = city_parts[0]
            remaining_city = ' '.join(city_parts[1:])
            new_name = f"{row['name']} {first_word}"
            return pd.Series([new_name, remaining_city])
        return pd.Series([row['name'], row['city']])

    df[['name', 'city']] = df.apply(update_name_city, axis=1)

    # Save to new CSV
    df.to_csv(output_file, index=False)



if __name__ == "__main__":
    # Install required packages if not already installed
    try:
        import PyPDF2
        import pandas as pd
        import requests
    except ImportError as e:
        print(f"Please install required packages: pip install PyPDF2 pandas requests")
        print(f"Missing package: {e}")
        exit(1)
    
    automate_shawnee()
    modify_csv("all_data_shawnee.csv", "all_data_shawnee.csv")
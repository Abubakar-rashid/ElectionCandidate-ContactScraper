from selenium import webdriver # done 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import re

def scrape_welaka_candidates():
    """
    Scrapes candidate information from Welaka Town Council election page
    Dynamically handles multiple candidates
    """
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Remove this line if you want to see the browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the page
        url = "https://soe.putnam-fl.gov/2025-Elections/2025-Town-of-Welaka-Candidate-Contact-List"
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  
        
        candidates = []
            
        # Method 3: Parse the entire page content and look for patterns
        if len(candidates) < 2:
            print("\nTrying Method 3: Full page text parsing...")
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            candidates_from_text = parse_candidates_from_text(page_text)
            
            for candidate in candidates_from_text:
                if candidate not in candidates:
                    candidates.append(candidate)
        
        # Method 4: Look for specific candidate containers or divs
        if len(candidates) < 2:
            print("\nTrying Method 4: Container-based detection...")
            
            # Look for divs that might contain multiple candidates
            potential_containers = driver.find_elements(By.XPATH, 
                "//div[contains(., 'Candidate Name') and contains(., 'Email')]")
            
            for container in potential_containers:
                text_content = container.text
                candidates_from_container = parse_candidates_from_text(text_content)
                
                for candidate in candidates_from_container:
                    if candidate not in candidates:
                        candidates.append(candidate)
        
        # Remove duplicates based on name
        unique_candidates = []
        seen_names = set()
        
        for candidate in candidates:
            name = candidate.get('name', '').strip()
            if name and name not in seen_names:
                unique_candidates.append(candidate)
                seen_names.add(name)
        
        candidates = unique_candidates
        
        print(f"\nTotal unique candidates found: {len(candidates)}")
        
        # Display the results
        for i, candidate in enumerate(candidates, 1):
            print(f"\n--- Candidate {i} ---")
            for key, value in candidate.items():
                print(f"{key.title()}: {value}")
        
        # Save to CSV
        if candidates:
            df = pd.DataFrame(candidates)
            df.to_csv("all_data_Putman.csv", index=False)
            print(f"\nData saved to all_data_Putman.csv")
        
        return candidates
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Take a screenshot for debugging
        driver.save_screenshot("error_screenshot.png")
        # Also save page source for debugging
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        return []
        
    finally:
        driver.quit()

def extract_candidate_from_container(container):
    """
    Extract candidate information from a container element
    """
    candidate_data = {}
    
    try:
        text_content = container.text
        lines = text_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Look for field patterns
            if "candidate name:" in line.lower():
                if ":" in line:
                    candidate_data["name"] = line.split(":", 1)[1].strip()
                elif i < len(lines) - 1:
                    candidate_data["name"] = lines[i + 1].strip()
                    
            elif "party" in line.lower() and ":" in line:
                candidate_data["party"] = line.split(":", 1)[1].strip()
            elif "party" in line.lower() and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if next_line and not ":" in next_line:
                    candidate_data["party"] = next_line
                    
            elif "address" in line.lower() and ":" in line:
                candidate_data["address"] = line.split(":", 1)[1].strip()
            elif "address" in line.lower() and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if next_line and not ":" in next_line:
                    candidate_data["address"] = next_line
                    
            elif "email" in line.lower() and ":" in line:
                candidate_data["email"] = line.split(":", 1)[1].strip()
            elif "email" in line.lower() and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if "@" in next_line:
                    candidate_data["email"] = next_line
                    
            elif "phone" in line.lower() and ":" in line:
                candidate_data["phone"] = line.split(":", 1)[1].strip()
            elif "phone" in line.lower() and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if re.match(r'[\d\-\(\)\s]+', next_line):
                    candidate_data["phone"] = next_line
                    
            elif "status" in line.lower() and ":" in line:
                candidate_data["status"] = line.split(":", 1)[1].strip()
            elif "status" in line.lower() and i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if next_line.upper() in ["QUALIFIED", "UNQUALIFIED", "PENDING"]:
                    candidate_data["status"] = next_line
                    
            elif "valid petitions" in line.lower():
                if ":" in line:
                    candidate_data["petitions"] = line.split(":", 1)[1].strip()
                elif i < len(lines) - 1:
                    next_line = lines[i + 1].strip()
                    if "of" in next_line.lower():
                        candidate_data["petitions"] = next_line
    
    except Exception as e:
        print(f"Error extracting from container: {str(e)}")
    
    return candidate_data if "name" in candidate_data else {}

def parse_candidates_from_text(text):
    """
    Parse candidate information from raw text content
    """
    candidates = []
    
    # Split text into potential candidate sections
    # Look for patterns that indicate a new candidate
    sections = re.split(r'(?=Candidate Name:|(?:^|\n)(?:[A-Z][a-z]+ ){2,})', text, flags=re.MULTILINE)
    
    for section in sections:
        if not section.strip():
            continue
            
        candidate_data = {}
        lines = section.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Extract information using regex patterns
            if re.search(r'candidate name:?\s*(.+)', line, re.IGNORECASE):
                match = re.search(r'candidate name:?\s*(.+)', line, re.IGNORECASE)
                candidate_data["name"] = match.group(1).strip()
                
            elif re.search(r'party:?\s*(.+)', line, re.IGNORECASE):
                match = re.search(r'party:?\s*(.+)', line, re.IGNORECASE)
                candidate_data["party"] = match.group(1).strip()
                
            elif re.search(r'address:?\s*(.+)', line, re.IGNORECASE):
                match = re.search(r'address:?\s*(.+)', line, re.IGNORECASE)
                candidate_data["address"] = match.group(1).strip()
                
            elif re.search(r'email:?\s*([^\s]+@[^\s]+)', line, re.IGNORECASE):
                match = re.search(r'email:?\s*([^\s]+@[^\s]+)', line, re.IGNORECASE)
                candidate_data["email"] = match.group(1).strip()
                
            elif re.search(r'phone:?\s*([\d\-\(\)\s]+)', line, re.IGNORECASE):
                match = re.search(r'phone:?\s*([\d\-\(\)\s]+)', line, re.IGNORECASE)
                candidate_data["phone"] = match.group(1).strip()
                
            elif re.search(r'status:?\s*(qualified|unqualified|pending)', line, re.IGNORECASE):
                match = re.search(r'status:?\s*(qualified|unqualified|pending)', line, re.IGNORECASE)
                candidate_data["status"] = match.group(1).strip()
                
            elif re.search(r'valid petitions:?\s*(\d+\s*of\s*\d+)', line, re.IGNORECASE):
                match = re.search(r'valid petitions:?\s*(\d+\s*of\s*\d+)', line, re.IGNORECASE)
                candidate_data["petitions"] = match.group(1).strip()
        
        if candidate_data and "name" in candidate_data:
            candidates.append(candidate_data)
    
    return candidates

def main():
    """
    Main function to run the scraper
    """
    print("Starting Welaka candidate scraper...")
    print("This script will try multiple methods to find all candidates on the page.")
    
    candidates = scrape_welaka_candidates()
    
    if candidates:
        print(f"\n Successfully scraped {len(candidates)} candidates!")
        print("\nSummary:")
        for i, candidate in enumerate(candidates, 1):
            name = candidate.get('name', 'Unknown')
            party = candidate.get('party', 'Unknown')
            print(f"{i}. {name} ({party})")
    else:
        print(" No candidates found. Check the website structure or connection.")

if __name__ == "__main__":
    main()
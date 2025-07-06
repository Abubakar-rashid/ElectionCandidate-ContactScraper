from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import os

class FloridaElectionsDownloader:
    def __init__(self, headless=False, download_dir=None):
        """
        Initialize the Florida Elections Downloader
        
        Args:
            headless (bool): Run browser in headless mode
            download_dir (str): Directory to save downloaded files
        """
        self.driver = None
        self.wait = None
        self.headless = headless
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'downloads')
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            
        # Set download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def get_current_election_year(self):
        """
        Get the current year - we want current year elections only
        """
        return datetime.datetime.now().year
    
    def navigate_to_page(self):
        """Navigate to the Florida elections candidate download page"""
        url = "https://dos.elections.myflorida.com/candidates/downloadcanlist.asp"
        print(f"Navigating to: {url}")
        self.driver.get(url)
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.ID, "wrapper")))
        print("Page loaded successfully")
        
    def get_current_year_elections(self):
        """
        Get all election options that contain the current year
        Returns list of tuples: (option_value, option_text)
        """
        try:
            # Find the election year dropdown
            election_year_select = Select(self.wait.until(
                EC.presence_of_element_located((By.NAME, "elecID"))
            ))
            
            current_year = self.get_current_election_year()
            
            # Get all available options
            all_options = [(option.get_attribute('value'), option.text.strip()) for option in election_year_select.options]
            print(f"All available election options: {len(all_options)} total")
            
            # Filter options that contain the current year
            current_year_elections = []
            for value, text in all_options:
                if str(current_year) in text and value:  # Skip empty values
                    current_year_elections.append((value, text))
            
            print(f"Found {len(current_year_elections)} elections for {current_year}:")
            for value, text in current_year_elections:
                print(f"  - {text} (value: {value})")
            
            return current_year_elections
            
        except Exception as e:
            print(f"Error getting current year elections: {e}")
            raise
    
    def select_election_by_value(self, election_value, election_text):
        """
        Select a specific election by its value
        
        Args:
            election_value (str): The value attribute of the option
            election_text (str): The text of the option (for logging)
        """
        try:
            # Find the election year dropdown
            election_year_select = Select(self.wait.until(
                EC.presence_of_element_located((By.NAME, "elecID"))
            ))
            
            # Select by value
            election_year_select.select_by_value(election_value)
            print(f"Selected election: {election_text}")
            time.sleep(1)  # Small delay after selection
            
        except Exception as e:
            print(f"Error selecting election '{election_text}': {e}")
            raise
    
    def select_office_type(self, office_type):
        """
        Select office type from dropdown
        
        Args:
            office_type (str): Type of office to select ('State Candidates', 'Local Candidates', etc.)
        """
        try:
            # Find the office type dropdown
            office_select = Select(self.wait.until(
                EC.presence_of_element_located((By.NAME, "cantype"))
            ))
            
            # Select the specified office type
            office_select.select_by_visible_text(office_type)
            print(f"  Selected office type: {office_type}")
            time.sleep(1)  # Small delay after selection
            
        except Exception as e:
            print(f"  Error selecting office type '{office_type}': {e}")
            raise
    
    def click_download_button(self):
        """Click the Download Candidate List button"""
        try:
            # Find and click the download button
            download_button = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "FormSubmit"))
            )
            
            print("  Clicking Download Candidate List button...")
            download_button.click()
            
            # Wait a moment for download to start
            time.sleep(3)
            print("  Download initiated")
            
        except Exception as e:
            print(f"  Error clicking download button: {e}")
            raise
    
    def download_for_all_current_year_elections(self, office_types=None):
        """
        Download candidate lists for all current year elections and specified office types
        
        Args:
            office_types (list): List of office types to download. 
                               If None, defaults to ['State Candidates', 'Local Candidates']
        """
        if office_types is None:
            office_types = ['State Candidates', 'Local Candidates']
        
        # Get all current year elections
        current_year_elections = self.get_current_year_elections()
        
        if not current_year_elections:
            print("No elections found for the current year!")
            return
        
        download_count = 0
        
        # Loop through each election
        for election_value, election_text in current_year_elections:
            print(f"\n=== Processing Election: {election_text} ===")
            
            try:
                # Select this election
                self.select_election_by_value(election_value, election_text)
                
                # Download for each office type
                for office_type in office_types:
                    try:
                        print(f"\n--- Downloading {office_type} for {election_text} ---")
                        
                        # Select the office type
                        self.select_office_type(office_type)
                        
                        # Click download button
                        self.click_download_button()
                        
                        download_count += 1
                        
                        # Wait between downloads to be respectful to the server
                        # time.sleep(2)
                        
                        print(f"   Successfully downloaded {office_type}")
                        
                    except Exception as e:
                        print(f"   Failed to download {office_type}: {e}")
                        continue
                
            except Exception as e:
                print(f"Failed to process election '{election_text}': {e}")
                continue
        
        print(f"\n=== Summary ===")
        print(f"Total downloads completed: {download_count}")
        print(f"Elections processed: {len(current_year_elections)}")
        print(f"Office types per election: {len(office_types)}")
    
    def run(self, office_types=None):
        """
        Main method to run the complete download process
        
        Args:
            office_types (list): List of office types to download
        """
        try:
            current_year = self.get_current_election_year()
            print("=== Florida Elections Candidate List Downloader ===")
            print(f"Target year: {current_year}")
            print(f"Download directory: {self.download_dir}")
            print(f"Office types: {office_types or ['State Candidates', 'Local Candidates']}")
            
            # Setup the driver
            self.setup_driver()
            
            # Navigate to the page
            self.navigate_to_page()
            
            # Download for all current year elections
            self.download_for_all_current_year_elections(office_types)
            
            print("\n=== Download process completed ===")
            
        except Exception as e:
            print(f"Error in main process: {e}")
            raise
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()

def main():
    """Main function to run the scraper"""
    
    # Configuration
    HEADLESS = True  # Set to True to run without GUI
    DOWNLOAD_DIR = os.getcwd()  # Directory to save files
    
    # Office types to download (you can modify this list)
    OFFICE_TYPES = [
        'State Candidates',
        'Local Candidates'
        # You can also use 'State & Local' to get both in one download
    ]
    
    # Create and run the downloader
    downloader = FloridaElectionsDownloader(
        headless=HEADLESS,
        download_dir=DOWNLOAD_DIR
    )
    
    try:
        downloader.run(OFFICE_TYPES)
    except Exception as e:
        print(f"Script failed: {e}")
import pandas as pd
import os
import glob
from pathlib import Path

def process_florida_candidate_files():
    """
    Dynamically processes all CandidateList.txt files and consolidates them into all_data_florida.csv
    """
    
    # Get the current directory (where the script is running)
    current_dir = Path.cwd()
    
    # Find all CandidateList files (both numbered and unnumbered)
    candidate_files = []
    
    # Look for CandidateList.txt files with various patterns
    patterns = [
        "CandidateList.txt",
        "CandidateList(*).txt",
        "candidatelist*.txt"  # in case of different capitalization
    ]
    
    for pattern in patterns:
        files = glob.glob(str(current_dir / pattern), recursive=False)
        candidate_files.extend(files)
    
    # Also check in florida_candidate_data subdirectory if it exists
    florida_data_dir = current_dir / "florida_candidate_data"
    if florida_data_dir.exists():
        for pattern in patterns:
            files = glob.glob(str(florida_data_dir / pattern), recursive=False)
            candidate_files.extend(files)
    
    # Remove duplicates and sort
    candidate_files = sorted(list(set(candidate_files)))
    
    print(f"Found {len(candidate_files)} candidate files:")
    for file in candidate_files:
        print(f"  - {os.path.basename(file)}")
    
    if not candidate_files:
        print("No CandidateList.txt files found!")
        return
    
    # List to store all dataframes
    all_dataframes = []
    
    # Process each file
    for file_path in candidate_files:
        try:
            print(f"\nProcessing: {os.path.basename(file_path)}")
            
            # Read the tab-separated file
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8', low_memory=False)
            
            # Add a source column to track which file the data came from
            df['SourceFile'] = os.path.basename(file_path)
            
            print(f"  - Loaded {len(df)} records")
            print(f"  - Columns: {list(df.columns)}")
            
            all_dataframes.append(df)
            
        except Exception as e:
            print(f"  - Error processing {file_path}: {str(e)}")
            continue
    
    if not all_dataframes:
        print("No valid data found in any files!")
        return
    
    # Combine all dataframes
    print(f"\nCombining {len(all_dataframes)} dataframes...")
    combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    
    print(f"Total records after combining: {len(combined_df)}")
    
    # Display basic statistics
    print(f"\nData Summary:")
    print(f"  - Total Records: {len(combined_df)}")
    print(f"  - Total Columns: {len(combined_df.columns)}")
    print(f"  - Unique Parties: {combined_df['PartyDesc'].nunique() if 'PartyDesc' in combined_df.columns else 'N/A'}")
    print(f"  - Unique Offices: {combined_df['OfficeDesc'].nunique() if 'OfficeDesc' in combined_df.columns else 'N/A'}")
    
    # Show party distribution if available
    if 'PartyDesc' in combined_df.columns:
        print(f"\nParty Distribution:")
        party_counts = combined_df['PartyDesc'].value_counts()
        for party, count in party_counts.head(10).items():
            print(f"  - {party}: {count}")
    
    # Save to CSV
    output_file = current_dir / "all_data_florida.csv"
    combined_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n Successfully saved consolidated data to: {output_file}")
    print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
    
    # Delete the processed txt files after successful consolidation
    print(f"\n Cleaning up processed files...")
    deleted_count = 0
    failed_deletions = []
    
    for file_path in candidate_files:
        try:
            os.remove(file_path)
            print(f"   Deleted: {os.path.basename(file_path)}")
            deleted_count += 1
        except Exception as e:
            print(f"   Failed to delete {os.path.basename(file_path)}: {str(e)}")
            failed_deletions.append(file_path)
    
    print(f"\nCleanup Summary:")
    print(f"  - Files successfully deleted: {deleted_count}")
    print(f"  - Files failed to delete: {len(failed_deletions)}")
    
    if failed_deletions:
        print(f"\nFiles that couldn't be deleted:")
        for file in failed_deletions:
            print(f"  - {os.path.basename(file)}")
    
    return combined_df

def analyze_florida_data(df=None):
    """
    Optional function to analyze the consolidated data
    """
    if df is None:
        # Try to load the consolidated file
        try:
            df = pd.read_csv("all_data_florida.csv")
        except FileNotFoundError:
            print("all_data_florida.csv not found. Run process_florida_candidate_files() first.")
            return
    
    print(" Florida Candidate Data Analysis")
    print("=" * 40)
    
    # Basic info
    print(f"Total Candidates: {len(df)}")
    print(f"Data Columns: {len(df.columns)}")
    
    # Office analysis
    if 'OfficeDesc' in df.columns:
        print(f"\n Top Offices by Candidate Count:")
        office_counts = df['OfficeDesc'].value_counts().head(10)
        for office, count in office_counts.items():
            print(f"  {office}: {count}")
    
    # Geographic analysis
    if 'County' in df.columns:
        print(f"\n Top Counties by Candidate Count:")
        county_counts = df['County'].value_counts().head(10)
        for county, count in county_counts.items():
            print(f"  {county}: {count}")
    
    # Status analysis
    if 'StatusDesc' in df.columns:
        print(f"\nCandidate Status Distribution:")
        status_counts = df['StatusDesc'].value_counts()
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

if __name__ == "__main__":
    main()
    print(" Florida Candidate Data Processor")
    print("=" * 40)
    
    # Process all candidate files
    consolidated_data = process_florida_candidate_files()
    
    if consolidated_data is not None:
        # Run analysis
        print("\n" + "=" * 40)
        analyze_florida_data(consolidated_data)
        
        print(f"\n Processing complete!")
        print(f"Check 'all_data_florida.csv' for the consolidated data.")
import pandas as pd
import os

# Define the standard column format
final_columns = [
    "First Name", "Last Name", "Email Address", "Phone Number",
    "Political Title", "State", "Address", "Party Affiliation"
]

# Helper function to load or create the final CSV
def load_or_create_final_csv(path="all_data.csv"):
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=final_columns)
    return df

# Helper function to load or create the data CSV
def load_or_create_data_csv(path="data.csv"):
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=final_columns)
    return df

# Helper function to normalize data types for consistent merging
def normalize_dataframe(df):
    # Ensure all columns are strings and handle NaN values
    df_normalized = df.copy()
    for col in final_columns:
        if col in df_normalized.columns:
            df_normalized[col] = df_normalized[col].astype(str).fillna('').replace('nan', '')
    return df_normalized

# Helper function to append data to final DataFrame, find new records, and deduplicate
def append_and_track_new_records(df_main, df_data, df_new):
    # Normalize all dataframes to ensure consistent data types
    df_main_norm = normalize_dataframe(df_main)
    df_new_norm = normalize_dataframe(df_new)
    
    # Find records that are not already in all_data.csv
    df_new_only = df_new_norm.merge(df_main_norm, on=final_columns, how='left', indicator=True)
    df_new_only = df_new_only[df_new_only['_merge'] == 'left_only'].drop('_merge', axis=1)
    
    # Add new records to both all_data and data (only if there are new records)
    if len(df_new_only) > 0:
        df_main_updated = pd.concat([df_main_norm, df_new_only], ignore_index=True)
        df_data_updated = pd.concat([normalize_dataframe(df_data), df_new_only], ignore_index=True)
    else:
        df_main_updated = df_main_norm
        df_data_updated = normalize_dataframe(df_data)
    
    return df_main_updated, df_data_updated, len(df_new_only)

# Load existing or create empty final DataFrames
df_all = load_or_create_final_csv()
df_data = load_or_create_data_csv()

total_new_records = 0

# ---------- Florida ----------
try:
    df_florida = pd.read_csv("all_data_florida.csv")
    allowed_statuses = ["Elected", "Defeated", "Qualified"]
    df_florida = df_florida[df_florida["StatusDesc"].isin(allowed_statuses)]
    df_florida["NameFirst"] = df_florida["NameFirst"].fillna('') + " " + df_florida["NameMiddle"].fillna('')
    df_florida["NameFirst"] = df_florida["NameFirst"].str.strip()
    df_florida = df_florida.rename(columns={
        "NameFirst": "First Name",
        "NameLast": "Last Name",
        "Email": "Email Address",
        "Phone": "Phone Number",
        "OfficeDesc": "Political Title",
        "State": "State",
        "Addr1": "Address",
        "PartyCode": "Party Affiliation"
    })
    df_florida = df_florida[final_columns]
    # Normalize data types before processing
    df_florida = normalize_dataframe(df_florida)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_florida)
    total_new_records += new_count
    print(f"Florida: {new_count} new records added")
except Exception as e:
    print("Florida:", e)

# ---------- Georgia ----------
try:
    df_georgia = pd.read_csv("all_data_georgia.csv")
    df_georgia[['Last Name', 'First Name']] = df_georgia['Name'].str.split(',', n=1, expand=True)
    df_georgia['First Name'] = df_georgia['First Name'].str.strip()
    df_georgia['Last Name'] = df_georgia['Last Name'].str.strip()
    df_georgia = df_georgia.rename(columns={
        "Candidate Email": "Email Address",
        "Office": "Political Title",
        "Candidate Address": "Address"
    })
    df_georgia.insert(3, "Phone Number", "")
    df_georgia.insert(5, "State", "Georgia")
    df_georgia["Party Affiliation"] = ""
    df_georgia = df_georgia[final_columns]
    # Normalize data types before processing
    df_georgia = normalize_dataframe(df_georgia)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_georgia)
    total_new_records += new_count
    print(f"Georgia: {new_count} new records added")
except Exception as e:
    print("Georgia:", e)

# ---------- Louisiana ----------
try:
    df_louisiana = pd.read_csv("all_data_louisiana.csv", usecols=[
        "BallotFirstName", "BallotLastName", "Email Address", "Phone", 
        "OfficeTitle", "State", "Address", "Party"
    ])
    df_louisiana = df_louisiana.rename(columns={
        "BallotFirstName": "First Name",
        "BallotLastName": "Last Name",
        "Phone": "Phone Number",
        "OfficeTitle": "Political Title",
        "Party": "Party Affiliation"
    })
    df_louisiana = df_louisiana[final_columns]
    # Normalize data types before processing
    df_louisiana = normalize_dataframe(df_louisiana)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_louisiana)
    total_new_records += new_count
    print(f"Louisiana: {new_count} new records added")
except Exception as e:
    print("Louisiana:", e)

# ---------- Putman ----------
try:
    df_putman = pd.read_csv("all_data_Putman.csv", usecols=["name", "email", "phone", "address", "party"])
    df_putman[['First Name', 'Last Name']] = df_putman['name'].str.strip().str.split(n=1, expand=True)
    df_putman = df_putman.drop(columns=["name"])
    df_putman = df_putman.rename(columns={
        "email": "Email Address",
        "phone": "Phone Number",
        "address": "Address",
        "party": "Party Affiliation"
    })
    df_putman.insert(4, "Political Title", "")
    df_putman.insert(5, "State", "")
    df_putman = df_putman[final_columns]
    # Normalize data types before processing
    df_putman = normalize_dataframe(df_putman)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_putman)
    total_new_records += new_count
    print(f"Putman: {new_count} new records added")
except Exception as e:
    print("Putman:", e)

# ---------- Shawnee ----------
try:
    df_shawnee = pd.read_csv("all_data_shawnee.csv", usecols=["name", "email", "phone", "office", "city", "address"])
    df_shawnee[['First Name', 'Last Name']] = df_shawnee['name'].str.strip().str.split(n=1, expand=True)
    df_shawnee = df_shawnee.drop(columns=["name"])
    df_shawnee = df_shawnee.rename(columns={
        "email": "Email Address",
        "phone": "Phone Number",
        "office": "Political Title",
        "city": "State",
        "address": "Address"
    })
    df_shawnee["Party Affiliation"] = ""
    df_shawnee = df_shawnee[final_columns]
    # Normalize data types before processing
    df_shawnee = normalize_dataframe(df_shawnee)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_shawnee)
    total_new_records += new_count
    print(f"Shawnee: {new_count} new records added")
except Exception as e:
    print("Shawnee:", e)

# ---------- South Carolina ----------
try:
    df_sc = pd.read_csv("all_data_SouthCarolina.csv", usecols=[
        "Candidate First Name", "Candidate Last Name", "Contact Email", 
        "Contact Phone Number", "Office", "Associated Counties", "Contact Address", "Party"
    ])
    df_sc = df_sc.rename(columns={
        "Candidate First Name": "First Name",
        "Candidate Last Name": "Last Name",
        "Contact Email": "Email Address",
        "Contact Phone Number": "Phone Number",
        "Office": "Political Title",
        "Associated Counties": "State",
        "Contact Address": "Address",
        "Party": "Party Affiliation"
    })
    df_sc = df_sc[final_columns]
    # Normalize data types before processing
    df_sc = normalize_dataframe(df_sc)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_sc)
    total_new_records += new_count
    print(f"South Carolina: {new_count} new records added")
except Exception as e:
    print("South Carolina:", e)

# ---------- Texas ----------
try:
    df_texas = pd.read_csv("all_data_texas.csv")
    df_texas = df_texas.rename(columns={
        "First Name": "First Name",
        "Last Name": "Last Name",
        "Email Address": "Email Address",
        "Phone Number": "Phone Number",
        "Political Title": "Political Title",
        "State": "State",
        "Address": "Address",
        "Party Affiliation": "Party Affiliation"
    })
    df_texas = df_texas[final_columns]
    # Normalize data types before processing
    df_texas = normalize_dataframe(df_texas)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_texas)
    total_new_records += new_count
    print(f"Texas: {new_count} new records added")
except Exception as e:
    print("Texas:", e)

# ---------- Virginia ----------
try:
    df_va = pd.read_csv("all_data_virginia.csv")
    df_va[['First Name', 'Last Name']] = df_va['Candidate Name'].str.strip().str.split(n=1, expand=True)
    df_va = df_va.rename(columns={
        "Email": "Email Address",
        "Phone": "Phone Number",
        "Office Title": "Political Title",
        "State": "State",
        "Address": "Address",
        "Political Party": "Party Affiliation"
    })
    df_va = df_va[final_columns]
    # Normalize data types before processing
    df_va = normalize_dataframe(df_va)
    df_all, df_data, new_count = append_and_track_new_records(df_all, df_data, df_va)
    total_new_records += new_count
    print(f"Virginia: {new_count} new records added")
except Exception as e:
    print("Virginia:", e)

# ---------- Save final combined CSVs ----------
df_all.to_csv("all_data.csv", index=False)
df_data.to_csv("data.csv", index=False)

print(f"\nProcessing complete!")
print(f"all_data.csv updated with {len(df_all)} total unique records.")
print(f"data.csv updated with {len(df_data)} total new records.")
print(f"This run added {total_new_records} new records.")
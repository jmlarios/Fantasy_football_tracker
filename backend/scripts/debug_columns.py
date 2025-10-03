"""Debug column names from FBref match page."""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import re

url = 'https://fbref.com/en/matches/6ca13ea8/Real-Betis-Alaves-August-22-2025-La-Liga'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print(f"Fetching: {url}\n")
r = requests.get(url, headers=headers)

soup = BeautifulSoup(r.content, 'lxml')

# Find summary stats tables
summary_tables = soup.find_all('table', {'id': re.compile(r'stats_.*_summary')})

print(f"Found {len(summary_tables)} summary tables\n")

for i, table in enumerate(summary_tables):
    caption = table.find('caption')
    if caption:
        print(f"Table {i}: {caption.text.strip()}")
    
    # Parse with pandas
    df = pd.read_html(StringIO(str(table)))[0]
    
    # Show column structure
    print(f"Columns type: {type(df.columns)}")
    print(f"Column names: {list(df.columns)}\n")
    
    # Handle multi-level columns
    if isinstance(df.columns, pd.MultiIndex):
        print("Multi-level columns:")
        for col in df.columns:
            print(f"  {col}")
        
        # Flatten
        df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]
        print(f"\nFlattened columns: {list(df.columns)}\n")
    
    # Show first few rows
    print("First 3 rows:")
    print(df.head(3))
    
    # Check for 'Min' column variations
    print("\nLooking for minutes column...")
    for col in df.columns:
        if 'min' in str(col).lower():
            print(f"  Found: {col}")
            print(f"  Sample values: {df[col].head(5).tolist()}")
    
    print("\n" + "="*80 + "\n")
    break  # Just check first table

"""Debug script to check FBref page structure."""
import requests
from bs4 import BeautifulSoup
import re

url = 'https://fbref.com/en/comps/12/2024-2025/schedule/2024-2025-La-Liga-Scores-and-Fixtures'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Fetching: {url}\n")
r = requests.get(url, headers=headers)
print(f"Status code: {r.status_code}\n")

soup = BeautifulSoup(r.content, 'lxml')

# Find the schedule table
schedule_table = soup.find('table', {'id': re.compile(r'^sched_.*')})

if schedule_table:
    print("✅ Found schedule table!")
    print(f"Table ID: {schedule_table.get('id')}\n")
    
    # Get all header cells
    header_row = schedule_table.find('thead').find('tr')
    headers = header_row.find_all('th')
    
    print("Column headers (data-stat attributes):")
    for i, th in enumerate(headers):
        data_stat = th.get('data-stat', 'NO DATA-STAT')
        text = th.text.strip()
        print(f"  {i}: data-stat='{data_stat}', text='{text}'")
    
    print("\n" + "="*60)
    print("Sample rows for matchday 10:")
    print("="*60 + "\n")
    
    tbody = schedule_table.find('tbody')
    rows = tbody.find_all('tr')
    
    matchday_10_count = 0
    for row in rows:
        # Get matchday
        matchday_cell = row.find('th', {'data-stat': 'gameweek'})
        if not matchday_cell:
            continue
        
        try:
            row_matchday = int(matchday_cell.text.strip())
        except (ValueError, AttributeError):
            continue
        
        if row_matchday == 10:
            matchday_10_count += 1
            
            # Extract info
            date_cell = row.find('td', {'data-stat': 'date'})
            home_cell = row.find('td', {'data-stat': 'home_team'})
            away_cell = row.find('td', {'data-stat': 'away_team'})
            score_cell = row.find('td', {'data-stat': 'score'})
            report_cell = row.find('td', {'data-stat': 'match_report'})
            
            print(f"Match {matchday_10_count}:")
            if date_cell:
                print(f"  Date: {date_cell.text.strip()}")
            if home_cell and away_cell:
                print(f"  Teams: {home_cell.text.strip()} vs {away_cell.text.strip()}")
            if score_cell:
                print(f"  Score: {score_cell.text.strip()}")
            if report_cell:
                link = report_cell.find('a')
                if link:
                    print(f"  Report: {link.get('href', 'NO HREF')}")
                else:
                    print(f"  Report: Not available yet")
            print()
    
    print(f"\nTotal matches found for matchday 10: {matchday_10_count}")
    
else:
    print("❌ Schedule table not found!")
    print("\nAvailable tables:")
    tables = soup.find_all('table')
    for i, table in enumerate(tables):
        print(f"  {i}: ID={table.get('id', 'NO ID')}")


"""Check which LaLiga seasons are available on FBref."""
import requests
from bs4 import BeautifulSoup

seasons_to_check = ["2025-2026", "2024-2025", "2023-2024"]

for season in seasons_to_check:
    url = f'https://fbref.com/en/comps/12/{season}/schedule/{season}-La-Liga-Scores-and-Fixtures'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    print(f"\nChecking {season}:")
    print(f"URL: {url}")
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'lxml')
            table = soup.find('table', {'id': lambda x: x and x.startswith('sched_')})
            
            if table:
                tbody = table.find('tbody')
                rows = tbody.find_all('tr') if tbody else []
                match_count = len([r for r in rows if r.find('td', {'data-stat': 'home_team'})])
                print(f"✅ Season AVAILABLE - Found {match_count} matches")
            else:
                print(f"⚠️ Page exists but no schedule table found")
        else:
            print(f"❌ Season NOT AVAILABLE")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*60)
print("RECOMMENDATION:")
print("Use the season that shows as AVAILABLE with match data.")
print("="*60)

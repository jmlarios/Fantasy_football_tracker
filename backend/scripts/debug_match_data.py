"""Debug a specific match to see the actual data structure."""
import sys
sys.path.insert(0, '/app')

from src.services.laliga_scraper import FBrefScraper

scraper = FBrefScraper(season="2025-2026")

# Get one match
matches = scraper.get_matches_for_matchday(2)
if matches:
    match = matches[0]
    print(f"Analyzing: {match['home_team']} vs {match['away_team']}")
    print(f"Score: {match['home_score']} - {match['away_score']}")
    print(f"URL: {match['match_report_url']}\n")
    
    stats = scraper.parse_match_stats(match['match_report_url'], match)
    
    print(f"Total players: {len(stats)}")
    
    # Check if any have minutes
    with_minutes = [s for s in stats if s['minutes_played'] > 0]
    print(f"Players with minutes > 0: {len(with_minutes)}")
    
    # Show top performers
    if with_minutes:
        print("\n🥅 Players with goals:")
        scorers = [s for s in with_minutes if s['goals'] > 0]
        for s in scorers:
            print(f"  {s['player_name']:20} ({s['team']:15}) - {s['goals']} goal(s), {s['minutes_played']} min")
        
        print("\n🎯 Players with assists:")
        assists = [s for s in with_minutes if s['assists'] > 0]
        for s in assists:
            print(f"  {s['player_name']:20} ({s['team']:15}) - {s['assists']} assist(s), {s['minutes_played']} min")
        
        print("\n⚠️ Cards:")
        cards = [s for s in with_minutes if s['yellow_cards'] > 0 or s['red_cards'] > 0]
        for s in cards:
            print(f"  {s['player_name']:20} ({s['team']:15}) - Yellow: {s['yellow_cards']}, Red: {s['red_cards']}")
        
        print("\n🧤 Goalkeepers:")
        gks = [s for s in with_minutes if s['saves'] > 0]
        for s in gks:
            print(f"  {s['player_name']:20} ({s['team']:15}) - {s['saves']} saves, Clean sheet: {s['clean_sheet']}")

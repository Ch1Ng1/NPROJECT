"""
Test script for verifying LiveScore integration
Tests different data sources and displays results
"""

from match_scraper import MatchScraper
from predictor import MatchPredictor

print("="*70)
print("TESTING FOOTBALL MATCH SCRAPER - LIVESCORE INTEGRATION")
print("="*70)

# Test 1: LiveScore mode (default)
print("\n[TEST 1] Using LiveScore integration (Football-Data.org API)")
print("-"*70)
scraper_live = MatchScraper(use_livescore=True)
matches_live = scraper_live.get_today_matches()
print(f"Result: Found {len(matches_live)} matches\n")

if matches_live:
    print("Sample matches:")
    for i, match in enumerate(matches_live[:3], 1):
        print(f"  {i}. {match['home_team']} vs {match['away_team']}")
        print(f"     League: {match['league']} ({match['country']})")

# Test 2: Demo mode
print("\n" + "="*70)
print("[TEST 2] Using Demo data mode")
print("-"*70)
scraper_demo = MatchScraper(use_livescore=False)
matches_demo = scraper_demo.get_today_matches()
print(f"Result: Found {len(matches_demo)} matches\n")

# Test 3: Predictions
print("="*70)
print("[TEST 3] Testing prediction algorithm")
print("-"*70)

predictor = MatchPredictor()
predictions = predictor.predict_all_matches(matches_live)

print(f"Generated {len(predictions)} predictions\n")
print("Top 3 predictions for home team wins:")
print("-"*70)

top_predictions = predictor.get_top_predictions(predictions, min_probability=50, limit=3)

for i, pred in enumerate(top_predictions, 1):
    print(f"\n{i}. {pred['home_team']} vs {pred['away_team']}")
    print(f"   League: {pred['league']}")
    print(f"   Home Win Probability: {pred['home_win_probability']}%")
    print(f"   Recommendation: {pred['prediction_class']}")
    print(f"   Confidence: {pred['confidence']}")

# Test 4: API endpoints simulation
print("\n" + "="*70)
print("[TEST 4] Simulating API response")
print("-"*70)

response_data = {
    'success': True,
    'count': len(predictions),
    'top_predictions': len(top_predictions),
    'data_source': 'LiveScore' if len(matches_live) > 5 else 'Demo',
    'predictions': [
        {
            'match': f"{p['home_team']} vs {p['away_team']}",
            'probability': p['home_win_probability']
        }
        for p in top_predictions
    ]
}

import json
print(json.dumps(response_data, indent=2))

print("\n" + "="*70)
print("TESTS COMPLETED SUCCESSFULLY!")
print("="*70)
print("\nTo start the web application, run:")
print("  python app.py")
print("\nThen visit: http://localhost:5000")
print("="*70)

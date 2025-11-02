#!/usr/bin/env python3
"""
Test ML Features
Test all ML/AI features with real HeatWave data
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ml_service.database import db
from ml_service.team_defense_analyzer import TeamDefenseAnalyzer
from ml_service.value_analyzer import ValueAnalyzer
from ml_service.injury_impact_analyzer import InjuryImpactAnalyzer
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and data availability"""
    print("\n" + "="*60)
    print("1. Testing Database Connection")
    print("="*60)
    
    if not db.test_connection():
        print("❌ Database connection failed")
        return False
    
    print("✅ Database connected successfully")
    
    # Check data availability
    summary = db.get_historical_data_summary()
    print("\n📊 Data Summary:")
    for table, count in summary.items():
        if table != 'error':
            print(f"   {table}: {count:,} records")
    
    return True

def test_team_defense_analyzer():
    """Test team defense analysis"""
    print("\n" + "="*60)
    print("2. Testing Team Defense Analyzer")
    print("="*60)
    
    try:
        analyzer = TeamDefenseAnalyzer()
        
        # Get defense stats
        print("   🏀 Calculating team defense statistics...")
        defense_stats = analyzer.get_team_defense_stats()
        
        if defense_stats.empty:
            print("   ⚠️ No defense stats available (may need more data)")
            return True
        
        print(f"   ✅ Calculated defense stats for {len(defense_stats)} team-position combinations")
        
        # Get rankings
        print("   📊 Getting defensive rankings...")
        rankings = analyzer.get_defensive_rankings()
        
        if not rankings.empty:
            print(f"   ✅ Rankings calculated for {len(rankings)} teams")
            print("\n   Top 5 Defensive Teams:")
            for idx, row in rankings.head(5).iterrows():
                team_name = row.get('name', row.get('abbreviation', 'Unknown'))
                fp_allowed = row.get('fantasy_points_allowed', 0)
                print(f"      {idx+1}. {team_name}: {fp_allowed:.2f} FP allowed")
        else:
            print("   ⚠️ No rankings available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_value_analyzer():
    """Test value analysis"""
    print("\n" + "="*60)
    print("3. Testing Value Analyzer")
    print("="*60)
    
    try:
        analyzer = ValueAnalyzer()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f"   💰 Analyzing value for {today}...")
        value_analysis = analyzer.get_value_analysis(today)
        
        if value_analysis.empty:
            print("   ⚠️ No value data available for today (may need DFS projections)")
            return True
        
        print(f"   ✅ Analyzed value for {len(value_analysis)} players")
        
        # Get best values
        print("   ⭐ Finding best value players...")
        best_values = analyzer.get_best_values(today, limit=10)
        
        if not best_values.empty:
            print(f"   ✅ Found {len(best_values)} best value players")
            print("\n   Top 5 Value Plays:")
            for idx, row in best_values.head(5).iterrows():
                name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                value_score = row.get('value_score', 0)
                salary = row.get('salary', 0)
                print(f"      {idx+1}. {name}: Value Score {value_score:.2f} (${salary:,})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_injury_impact_analyzer():
    """Test injury impact analysis"""
    print("\n" + "="*60)
    print("4. Testing Injury Impact Analyzer")
    print("="*60)
    
    try:
        analyzer = InjuryImpactAnalyzer()
        
        # Get all active injuries
        print("   🏥 Getting all active injuries...")
        all_impacts = analyzer.get_all_active_injuries_impact()
        
        if all_impacts.empty:
            print("   ℹ️ No active injuries found (this is actually good!)")
            return True
        
        print(f"   ✅ Found {len(all_impacts)} active injuries with impact analysis")
        
        # Show top impacts
        if len(all_impacts) > 0:
            print("\n   Top Impact Injuries:")
            for idx, row in all_impacts.head(5).iterrows():
                player_name = row.get('player_name', 'Unknown')
                impact = row.get('impact_level', 'UNKNOWN')
                replacement = row.get('best_replacement', 'None')
                print(f"      {idx+1}. {player_name}: {impact} impact → {replacement}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all ML feature tests"""
    print("\n" + "="*60)
    print("ML/AI Features Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Database connection
    results.append(("Database Connection", test_database_connection()))
    
    # Test 2: Team Defense Analyzer
    if results[-1][1]:  # Only run if DB connection works
        results.append(("Team Defense Analyzer", test_team_defense_analyzer()))
    
    # Test 3: Value Analyzer
    if results[0][1]:  # Only run if DB connection works
        results.append(("Value Analyzer", test_value_analyzer()))
    
    # Test 4: Injury Impact Analyzer
    if results[0][1]:  # Only run if DB connection works
        results.append(("Injury Impact Analyzer", test_injury_impact_analyzer()))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests had issues (may be due to insufficient data)")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())


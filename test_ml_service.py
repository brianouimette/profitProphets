#!/usr/bin/env python3
"""
Test ML Service
Test the ML service with current data to verify everything works
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ml_service.team_defense_analyzer import analyze_team_defense
from ml_service.database import db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and data availability"""
    print("🔌 Testing database connection...")
    
    try:
        # Test basic connection
        players = db.get_players(limit=5)
        print(f"✅ Players: {len(players)} records")
        
        teams = db.get_teams()
        print(f"✅ Teams: {len(teams)} records")
        
        games = db.get_games(limit=5)
        print(f"✅ Games: {len(games)} records")
        
        game_logs = db.get_player_game_logs(limit=5)
        print(f"✅ Game Logs: {len(game_logs)} records")
        
        # Get data summary
        summary = db.get_historical_data_summary()
        print(f"📊 Data Summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_team_defense_analysis():
    """Test team defense analysis"""
    print("\n🏀 Testing team defense analysis...")
    
    try:
        # Run team defense analysis
        results = analyze_team_defense()
        
        print(f"📊 Defense Stats: {results['defense_stats'].shape}")
        print(f"📈 Rankings: {results['rankings'].shape}")
        print(f"📋 Position Summary: {results['position_summary'].shape}")
        
        # Show sample results
        if not results['defense_stats'].empty:
            print("\n🔍 Sample Defense Stats:")
            print(results['defense_stats'].head())
        
        if not results['rankings'].empty:
            print("\n🏆 Top 5 Defensive Teams:")
            print(results['rankings'].head())
        
        return True
        
    except Exception as e:
        print(f"❌ Team defense analysis failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 NBA Fantasy Optimizer ML Service Test")
    print("=" * 50)
    
    # Test 1: Database connection
    db_ok = test_database_connection()
    if not db_ok:
        print("❌ Database tests failed - check your Supabase configuration")
        return 1
    
    # Test 2: Team defense analysis
    analysis_ok = test_team_defense_analysis()
    if not analysis_ok:
        print("❌ Team defense analysis failed - check your data")
        return 1
    
    print("\n✅ All tests passed! ML service is ready.")
    print("\n🚀 Next steps:")
    print("   1. Analyze your historical data: python analyze_historical_data.py")
    print("   2. Start the ML API: python -m ml_service.api")
    print("   3. Test API endpoints: curl http://localhost:8001/health")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

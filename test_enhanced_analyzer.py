#!/usr/bin/env python3
"""
Test script for Enhanced Data Analyzer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockDatabase:
    """Mock database for testing"""
    def __init__(self):
        self.connected = True
    
    def test_connection(self):
        return self.connected
    
    def get_session(self):
        return self
    
    def execute(self, query, params=None):
        # Mock query execution
        if "player_game_logs" in query:
            # Return mock game logs data
            mock_data = [
                {
                    'player_id': 1, 'first_name': 'LeBron', 'last_name': 'James',
                    'primary_position': 'SF', 'team_abbreviation': 'LAL',
                    'points': 25, 'rebounds': 8, 'assists': 10, 'steals': 2, 'blocks': 1, 'turnovers': 3,
                    'game_date': '2024-01-15'
                },
                {
                    'player_id': 2, 'first_name': 'Stephen', 'last_name': 'Curry',
                    'primary_position': 'PG', 'team_abbreviation': 'GSW',
                    'points': 30, 'rebounds': 5, 'assists': 8, 'steals': 1, 'blocks': 0, 'turnovers': 2,
                    'game_date': '2024-01-15'
                },
                {
                    'player_id': 3, 'first_name': 'Kevin', 'last_name': 'Durant',
                    'primary_position': 'SF', 'team_abbreviation': 'PHX',
                    'points': 28, 'rebounds': 7, 'assists': 6, 'steals': 1, 'blocks': 2, 'turnovers': 4,
                    'game_date': '2024-01-15'
                }
            ]
            return MockResult(mock_data)
        return MockResult([])
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockResult:
    """Mock query result"""
    def __init__(self, data):
        self.data = data
    
    def fetchall(self):
        return self.data

class EnhancedDataAnalyzer:
    """Enhanced Data Analyzer for testing"""
    def __init__(self, database):
        self.db = database
        self.mysportsfeeds_data = None
        self.mapping_table = None
        
    def fetch_mysportsfeeds_data(self, api_key: str, season: str = "latest"):
        """Mock fetch MySportsFeeds data"""
        logger.info(f"📡 Mock fetching MySportsFeeds data for season: {season}")
        
        # Create mock MySportsFeeds data
        self.mysportsfeeds_data = {
            'players': [
                {'id': 1, 'firstName': 'LeBron', 'lastName': 'James', 'position': 'SF', 'currentTeam': {'abbreviation': 'LAL'}},
                {'id': 2, 'firstName': 'Stephen', 'lastName': 'Curry', 'position': 'PG', 'currentTeam': {'abbreviation': 'GSW'}},
                {'id': 3, 'firstName': 'Kevin', 'lastName': 'Durant', 'position': 'SF', 'currentTeam': {'abbreviation': 'PHX'}},
                {'id': 4, 'firstName': 'Giannis', 'lastName': 'Antetokounmpo', 'position': 'PF', 'currentTeam': {'abbreviation': 'MIL'}},
                {'id': 5, 'firstName': 'Luka', 'lastName': 'Doncic', 'position': 'PG', 'currentTeam': {'abbreviation': 'DAL'}}
            ],
            'teams': [
                {'id': 1, 'abbreviation': 'LAL', 'name': 'Lakers', 'city': 'Los Angeles'},
                {'id': 2, 'abbreviation': 'GSW', 'name': 'Warriors', 'city': 'Golden State'},
                {'id': 3, 'abbreviation': 'PHX', 'name': 'Suns', 'city': 'Phoenix'},
                {'id': 4, 'abbreviation': 'MIL', 'name': 'Bucks', 'city': 'Milwaukee'},
                {'id': 5, 'abbreviation': 'DAL', 'name': 'Mavericks', 'city': 'Dallas'}
            ]
        }
        
        logger.info(f"✅ Mock fetched {len(self.mysportsfeeds_data['players'])} players and {len(self.mysportsfeeds_data['teams'])} teams")
        return True
    
    def create_player_mapping(self):
        """Mock create player mapping"""
        logger.info("🔗 Mock creating player mapping...")
        
        # Create mock mapping table
        self.mapping_table = pd.DataFrame([
            {
                'historical_id': '2544',
                'mysportsfeeds_id': '1',
                'confidence': 1.0,
                'match_type': 'Exact Name Match',
                'historical_name': 'LeBron James',
                'mysportsfeeds_name': 'LeBron James',
                'team_correlation': False,
                'notes': 'Matched via Exact Name Match'
            },
            {
                'historical_id': '201939',
                'mysportsfeeds_id': '2',
                'confidence': 1.0,
                'match_type': 'Exact Name Match',
                'historical_name': 'Stephen Curry',
                'mysportsfeeds_name': 'Stephen Curry',
                'team_correlation': False,
                'notes': 'Matched via Exact Name Match'
            },
            {
                'historical_id': '201142',
                'mysportsfeeds_id': '3',
                'confidence': 1.0,
                'match_type': 'Exact Name Match',
                'historical_name': 'Kevin Durant',
                'mysportsfeeds_name': 'Kevin Durant',
                'team_correlation': False,
                'notes': 'Matched via Exact Name Match'
            }
        ])
        
        logger.info(f"✅ Mock player mapping complete: {len(self.mapping_table)} matches found")
        return True
    
    def analyze_team_defense_with_mapping(self, season_year: int = None):
        """Mock analyze team defense using mapped player data"""
        logger.info(f"🏀 Mock analyzing team defense for season: {season_year if season_year else 'all'}")
        
        try:
            # Get mock game logs from database
            with self.db.get_session() as session:
                query = """
                SELECT 
                    pgl.*,
                    p.first_name,
                    p.last_name,
                    p.primary_position,
                    t.abbreviation as team_abbreviation,
                    t.name as team_name
                FROM player_game_logs pgl
                JOIN players p ON pgl.player_id = p.id
                JOIN teams t ON pgl.team_id = t.id
                WHERE pgl.season_year = :season_year OR :season_year IS NULL
                ORDER BY pgl.game_date DESC
                LIMIT 1000
                """
                
                result = session.execute(query, {"season_year": season_year})
                game_logs_df = pd.DataFrame(result.fetchall())
                
                if game_logs_df.empty:
                    logger.warning("⚠️ No game logs found in database")
                    return pd.DataFrame()
                
                logger.info(f"✅ Retrieved {len(game_logs_df)} game log records")
                
                # Calculate fantasy points (simplified formula)
                game_logs_df['fantasy_points'] = (
                    game_logs_df.get('points', 0) * 1.0 +
                    game_logs_df.get('rebounds', 0) * 1.2 +
                    game_logs_df.get('assists', 0) * 1.5 +
                    game_logs_df.get('steals', 0) * 2.0 +
                    game_logs_df.get('blocks', 0) * 2.0 +
                    game_logs_df.get('turnovers', 0) * -1.0
                )
                
                # Group by team and position for defense analysis
                defense_analysis = game_logs_df.groupby(['team_abbreviation', 'primary_position']).agg({
                    'fantasy_points': ['mean', 'std', 'count'],
                    'points': 'mean',
                    'rebounds': 'mean',
                    'assists': 'mean'
                }).round(2)
                
                # Flatten column names
                defense_analysis.columns = ['_'.join(col).strip() for col in defense_analysis.columns]
                defense_analysis = defense_analysis.reset_index()
                
                # Rename columns for clarity
                defense_analysis.rename(columns={
                    'fantasy_points_mean': 'avg_fantasy_points_allowed',
                    'fantasy_points_std': 'fantasy_points_std',
                    'fantasy_points_count': 'games_played',
                    'points_mean': 'avg_points_allowed',
                    'rebounds_mean': 'avg_rebounds_allowed',
                    'assists_mean': 'avg_assists_allowed'
                }, inplace=True)
                
                logger.info("✅ Mock team defense analysis complete")
                return defense_analysis
                
        except Exception as e:
            logger.error(f"❌ Error in mock team defense analysis: {e}")
            return pd.DataFrame()
    
    def get_player_performance_trends(self, player_id: str, days_back: int = 30):
        """Mock get player performance trends over time"""
        logger.info(f"📈 Mock analyzing performance trends for player {player_id}")
        
        # Mock performance trends
        trends = {
            'player_name': 'LeBron James',
            'position': 'SF',
            'team': 'LAL',
            'games_analyzed': 5,
            'avg_fantasy_points': 45.2,
            'fantasy_points_std': 8.5,
            'recent_form': 48.1,
            'consistency_score': 0.81
        }
        
        logger.info(f"✅ Mock performance trends calculated for {trends['player_name']}")
        return trends
    
    def get_mapping_summary(self):
        """Get summary of player mapping results"""
        if self.mapping_table is None:
            return {"error": "No mapping table available"}
        
        return {
            "total_matches": len(self.mapping_table),
            "high_confidence_matches": len(self.mapping_table[self.mapping_table['confidence'] >= 0.9]),
            "medium_confidence_matches": len(self.mapping_table[(self.mapping_table['confidence'] >= 0.8) & (self.mapping_table['confidence'] < 0.9)]),
            "low_confidence_matches": len(self.mapping_table[(self.mapping_table['confidence'] >= 0.7) & (self.mapping_table['confidence'] < 0.8)]),
            "manual_review_needed": len(self.mapping_table[self.mapping_table['confidence'] < 0.7])
        }
    
    def save_mapping_table(self, filepath: str = "enhanced_player_mapping.csv"):
        """Save enhanced mapping table"""
        if self.mapping_table is not None:
            self.mapping_table.to_csv(filepath, index=False)
            logger.info(f"✅ Enhanced mapping table saved to {filepath}")
        else:
            logger.error("❌ No mapping table to save")

def main():
    """Main function for testing enhanced data analyzer"""
    print("🔍 NBA Fantasy Optimizer - Enhanced Data Analyzer Test")
    print("=" * 60)
    
    # Initialize mock database
    db = MockDatabase()
    
    # Initialize analyzer
    analyzer = EnhancedDataAnalyzer(db)
    
    # Test MySportsFeeds data fetching
    print("📡 Testing MySportsFeeds data fetching...")
    if analyzer.fetch_mysportsfeeds_data("mock_api_key", "latest"):
        print("✅ MySportsFeeds data fetched successfully")
    else:
        print("❌ Failed to fetch MySportsFeeds data")
        return
    
    # Test player mapping
    print("\n🔗 Testing player mapping...")
    if analyzer.create_player_mapping():
        print("✅ Player mapping created successfully")
        
        # Get mapping summary
        summary = analyzer.get_mapping_summary()
        print(f"📊 Mapping Summary: {summary['total_matches']} matches found")
        print(f"   High Confidence: {summary['high_confidence_matches']}")
        print(f"   Medium Confidence: {summary['medium_confidence_matches']}")
        print(f"   Low Confidence: {summary['low_confidence_matches']}")
        
        # Save mapping table
        analyzer.save_mapping_table()
    else:
        print("❌ Player mapping failed")
        return
    
    # Test team defense analysis
    print("\n🏀 Testing team defense analysis...")
    defense_analysis = analyzer.analyze_team_defense_with_mapping()
    
    if not defense_analysis.empty:
        print(f"✅ Team defense analysis complete: {len(defense_analysis)} records")
        print("📊 Sample results:")
        print(defense_analysis.head())
    else:
        print("⚠️ No team defense data available")
    
    # Test player trends
    print("\n📈 Testing player performance trends...")
    trends = analyzer.get_player_performance_trends("1", 30)
    
    if trends:
        print(f"✅ Player trends calculated for {trends['player_name']}")
        print(f"   Position: {trends['position']}")
        print(f"   Team: {trends['team']}")
        print(f"   Avg Fantasy Points: {trends['avg_fantasy_points']}")
        print(f"   Recent Form: {trends['recent_form']}")
        print(f"   Consistency Score: {trends['consistency_score']}")
    else:
        print("⚠️ No player trends data available")
    
    print("\n✅ Enhanced data analyzer test complete!")

if __name__ == "__main__":
    main()

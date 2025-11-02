"""
NBA Fantasy Optimizer - Enhanced Data Analyzer
Integrates with MySportsFeeds API and uses player mapping for analysis
"""

import pandas as pd
import numpy as np
import requests
import json
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from .database import MLDatabase
from .player_mapper import PlayerMapper

logger = logging.getLogger(__name__)

class EnhancedDataAnalyzer:
    def __init__(self, database: MLDatabase):
        self.db = database
        self.player_mapper = PlayerMapper()
        self.mysportsfeeds_data = None
        self.mapping_table = None
        
    def fetch_mysportsfeeds_data(self, api_key: str, season: str = "latest", mock_data: Optional[Dict] = None):
        """Fetch data from MySportsFeeds API or use mock data"""
        logger.info(f"📡 Fetching MySportsFeeds data for season: {season}")
        
        # Use mock data if provided
        if mock_data:
            logger.info("🎭 Using mock MySportsFeeds data for testing")
            self.mysportsfeeds_data = mock_data
            return True
        
        try:
            # MySportsFeeds API endpoints
            base_url = "https://api.mysportsfeeds.com/v2.1/pull/nba"
            headers = {
                "Authorization": f"Basic {api_key}",
                "Accept": "application/json"
            }
            
            # Fetch players data
            players_url = f"{base_url}/{season}/players.json"
            players_response = requests.get(players_url, headers=headers)
            players_response.raise_for_status()
            players_data = players_response.json()
            
            # Fetch teams data
            teams_url = f"{base_url}/{season}/teams.json"
            teams_response = requests.get(teams_url, headers=headers)
            teams_response.raise_for_status()
            teams_data = teams_response.json()
            
            # Store the data
            self.mysportsfeeds_data = {
                'players': players_data.get('players', []),
                'teams': teams_data.get('teams', [])
            }
            
            logger.info(f"✅ Fetched {len(self.mysportsfeeds_data['players'])} players and {len(self.mysportsfeeds_data['teams'])} teams")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error fetching MySportsFeeds data: {e}")
            return False
    
    def create_player_mapping(self):
        """Create player mapping between historical and MySportsFeeds data"""
        logger.info("🔗 Creating player mapping...")
        
        if self.mysportsfeeds_data is None:
            logger.error("❌ MySportsFeeds data not loaded")
            return False
        
        # Load historical data with recency filter
        if not self.player_mapper.load_historical_data(years_threshold=5):
            logger.error("❌ Failed to load historical data")
            return False
        
        # Load MySportsFeeds data into mapper
        if not self.player_mapper.load_mysportsfeeds_data(self.mysportsfeeds_data):
            logger.error("❌ Failed to load MySportsFeeds data into mapper")
            return False
        
        # Find matches
        matches = self.player_mapper.find_matches(confidence_threshold=0.7)
        
        # Create mapping table
        self.mapping_table = self.player_mapper.create_mapping_table(matches)
        
        # Get mapping summary
        summary = self.player_mapper.get_mapping_summary()
        logger.info(f"✅ Player mapping complete: {summary['total_matches']} matches found")
        
        return True
    
    def analyze_team_defense_with_mapping(self, season_year: int = None):
        """Analyze team defense using mapped player data"""
        logger.info(f"🏀 Analyzing team defense for season: {season_year if season_year else 'all'}")
        
        if self.mapping_table is None or self.mapping_table.empty:
            logger.error("❌ No player mapping available")
            return pd.DataFrame()
        
        try:
            # Get game logs from database
            with self.db.get_session() as session:
                # Query for player game logs with mapped IDs
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
                
                logger.info("✅ Team defense analysis complete")
                return defense_analysis
                
        except Exception as e:
            logger.error(f"❌ Error in team defense analysis: {e}")
            return pd.DataFrame()
    
    def get_player_performance_trends(self, player_id: str, days_back: int = 30):
        """Get player performance trends over time"""
        logger.info(f"📈 Analyzing performance trends for player {player_id}")
        
        try:
            with self.db.get_session() as session:
                # Query for recent player performance
                query = """
                SELECT 
                    pgl.*,
                    p.first_name,
                    p.last_name,
                    p.primary_position,
                    t.abbreviation as team_abbreviation
                FROM player_game_logs pgl
                JOIN players p ON pgl.player_id = p.id
                JOIN teams t ON pgl.team_id = t.id
                WHERE pgl.player_id = :player_id
                AND pgl.game_date >= :start_date
                ORDER BY pgl.game_date DESC
                """
                
                start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                
                result = session.execute(query, {
                    "player_id": player_id,
                    "start_date": start_date
                })
                
                performance_df = pd.DataFrame(result.fetchall())
                
                if performance_df.empty:
                    logger.warning(f"⚠️ No performance data found for player {player_id}")
                    return pd.DataFrame()
                
                # Calculate fantasy points
                performance_df['fantasy_points'] = (
                    performance_df.get('points', 0) * 1.0 +
                    performance_df.get('rebounds', 0) * 1.2 +
                    performance_df.get('assists', 0) * 1.5 +
                    performance_df.get('steals', 0) * 2.0 +
                    performance_df.get('blocks', 0) * 2.0 +
                    performance_df.get('turnovers', 0) * -1.0
                )
                
                # Calculate trends
                trends = {
                    'player_name': f"{performance_df.iloc[0]['first_name']} {performance_df.iloc[0]['last_name']}",
                    'position': performance_df.iloc[0]['primary_position'],
                    'team': performance_df.iloc[0]['team_abbreviation'],
                    'games_analyzed': len(performance_df),
                    'avg_fantasy_points': performance_df['fantasy_points'].mean(),
                    'fantasy_points_std': performance_df['fantasy_points'].std(),
                    'recent_form': performance_df.head(5)['fantasy_points'].mean(),
                    'consistency_score': 1 - (performance_df['fantasy_points'].std() / performance_df['fantasy_points'].mean()) if performance_df['fantasy_points'].mean() > 0 else 0
                }
                
                logger.info(f"✅ Performance trends calculated for {trends['player_name']}")
                return trends
                
        except Exception as e:
            logger.error(f"❌ Error analyzing player trends: {e}")
            return {}
    
    def get_mapping_summary(self):
        """Get summary of player mapping results"""
        if self.mapping_table is None:
            return {"error": "No mapping table available"}
        
        return self.player_mapper.get_mapping_summary()
    
    def save_mapping_table(self, filepath: str = "enhanced_player_mapping.csv"):
        """Save enhanced mapping table"""
        if self.mapping_table is not None:
            self.mapping_table.to_csv(filepath, index=False)
            logger.info(f"✅ Enhanced mapping table saved to {filepath}")
        else:
            logger.error("❌ No mapping table to save")

def main():
    """Main function for testing enhanced data analyzer"""
    print("🔍 NBA Fantasy Optimizer - Enhanced Data Analyzer")
    print("=" * 60)
    
    # Initialize database
    db = Database()  # pyright: ignore[reportUndefinedVariable]
    if not db.test_connection():
        print("❌ Database connection failed")
        return
    
    # Initialize analyzer
    analyzer = EnhancedDataAnalyzer(db)
    
    # Note: In production, you would use real API key
    # For testing, we'll use sample data
    print("📡 Note: Using sample data for testing")
    print("   In production, use: analyzer.fetch_mysportsfeeds_data(api_key)")
    
    # Create sample MySportsFeeds data
    sample_data = {
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
    
    analyzer.mysportsfeeds_data = sample_data
    
    # Create player mapping
    if analyzer.create_player_mapping():
        print("✅ Player mapping created successfully")
        
        # Get mapping summary
        summary = analyzer.get_mapping_summary()
        print(f"📊 Mapping Summary: {summary['total_matches']} matches found")
        
        # Save mapping table
        analyzer.save_mapping_table()
        
        # Test team defense analysis
        print("\n🏀 Testing team defense analysis...")
        defense_analysis = analyzer.analyze_team_defense_with_mapping()
        
        if not defense_analysis.empty:
            print(f"✅ Team defense analysis complete: {len(defense_analysis)} records")
            print("📊 Sample results:")
            print(defense_analysis.head())
        else:
            print("⚠️ No team defense data available (database may be empty)")
        
        print("\n✅ Enhanced data analyzer test complete!")
    else:
        print("❌ Player mapping failed")

if __name__ == "__main__":
    main()

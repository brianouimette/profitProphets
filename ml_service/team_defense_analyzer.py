"""
Team Defense Analysis
Analyzes team defensive performance by position for fantasy points allowed
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from ml_service.database import db
from ml_service.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamDefenseAnalyzer:
    """Analyzes team defensive performance for fantasy sports"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.defense_stats = {}
        self.position_mapping = {
            'PG': 'Guard',
            'SG': 'Guard', 
            'SF': 'Forward',
            'PF': 'Forward',
            'C': 'Center'
        }
    
    def get_team_defense_stats(self, season: Optional[str] = None) -> pd.DataFrame:
        """Calculate team defense statistics by position"""
        logger.info("🏀 Calculating team defense statistics...")
        
        try:
            # Get player game logs
            game_logs = db.get_player_game_logs()
            if game_logs.empty:
                logger.warning("No player game logs found")
                return pd.DataFrame()
            
            # Get games data
            games = db.get_games(season=season)
            if games.empty:
                logger.warning("No games data found")
                return pd.DataFrame()
            
            # Get players data for position mapping
            players = db.get_players()
            if players.empty:
                logger.warning("No players data found")
                return pd.DataFrame()
            
            # Merge data
            merged_data = self._merge_game_data(game_logs, games, players)
            if merged_data.empty:
                logger.warning("No merged data available")
                return pd.DataFrame()
            
            # Calculate defense stats
            defense_stats = self._calculate_defense_stats(merged_data)
            
            logger.info(f"✅ Team defense stats calculated for {len(defense_stats)} team-position combinations")
            return defense_stats
            
        except Exception as e:
            logger.error(f"Error calculating team defense stats: {e}")
            return pd.DataFrame()
    
    def _merge_game_data(self, game_logs: pd.DataFrame, games: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
        """Merge game logs with games and players data"""
        try:
            # Get game lineups to determine which team each player was on
            lineups = db.get_game_lineups()
            
            # Merge game logs with games to get home/away teams
            merged = game_logs.merge(
                games[['id', 'away_team_id', 'home_team_id', 'game_date']], 
                left_on='game_id', 
                right_on='id', 
                how='left'
            )
            
            # Merge with lineups to get the player's team for this game
            if not lineups.empty:
                merged = merged.merge(
                    lineups[['game_id', 'player_id', 'team_id']],
                    on=['game_id', 'player_id'],
                    how='left'
                )
            else:
                # Fallback: use player's current team if lineups not available
                merged = merged.merge(
                    players[['id', 'current_team_id']],
                    left_on='player_id',
                    right_on='id',
                    how='left',
                    suffixes=('', '_player')
                )
                merged['team_id'] = merged['current_team_id']
            
            # Merge with players for position data
            merged = merged.merge(
                players[['id', 'primary_position']], 
                left_on='player_id', 
                right_on='id', 
                how='left',
                suffixes=('', '_pos')
            )
            
            # Determine opponent team: if player's team is home, opponent is away; if away, opponent is home
            def get_opponent(row):
                if pd.isna(row.get('team_id')):
                    return None
                if row['team_id'] == row['home_team_id']:
                    return row['away_team_id']
                elif row['team_id'] == row['away_team_id']:
                    return row['home_team_id']
                return None
            
            merged['opponent_team_id'] = merged.apply(get_opponent, axis=1)
            
            # Filter out rows where we couldn't determine opponent
            merged = merged[merged['opponent_team_id'].notna()]
            
            # Add position category
            merged['position_category'] = merged['primary_position'].map(self.position_mapping)
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging game data: {e}")
            return pd.DataFrame()
    
    def _calculate_defense_stats(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate defensive statistics for each team-position combination"""
        try:
            # Calculate points from field goals and free throws (if not directly available)
            if 'field_goals_made' in data.columns and 'three_pointers_made' in data.columns and 'free_throws_made' in data.columns:
                data['points'] = (
                    (data['field_goals_made'] - data['three_pointers_made']) * 2 +
                    data['three_pointers_made'] * 3 +
                    data['free_throws_made']
                )
            
            # Group by opponent team and position
            agg_dict = {
                'fantasy_points': ['mean', 'std', 'count', 'sum']
            }
            
            # Add other stat aggregations if columns exist
            stat_columns = ['rebounds', 'assists', 'steals', 'blocks', 'points']
            for col in stat_columns:
                if col in data.columns:
                    agg_dict[col] = ['mean', 'std']
            
            defense_groups = data.groupby(['opponent_team_id', 'position_category']).agg(agg_dict).reset_index()
            
            # Flatten column names
            cols = ['team_id', 'position']
            for col in agg_dict.keys():
                cols.append(f'{col}_allowed')
                cols.append(f'{col}_std')
                if col == 'fantasy_points':
                    cols.extend(['games_played', f'total_{col}'])
            
            defense_groups.columns = cols[:len(defense_groups.columns)]
            
            # Calculate additional metrics
            if 'total_fantasy_points' in defense_groups.columns and 'games_played' in defense_groups.columns:
                defense_groups['fantasy_points_per_game'] = (
                    defense_groups['total_fantasy_points'] / defense_groups['games_played']
                )
            
            # Normalized defensive rating (lower fantasy points allowed = better defense)
            if 'fantasy_points_allowed' in defense_groups.columns:
                defense_groups['defensive_rating'] = 100 - (
                    (defense_groups['fantasy_points_allowed'] / 50) * 100
                ).clip(0, 100)
            
            # Add team names
            teams = db.get_teams()
            if not teams.empty:
                defense_groups = defense_groups.merge(
                    teams[['id', 'abbreviation', 'city', 'name']], 
                    left_on='team_id', 
                    right_on='id', 
                    how='left'
                )
            
            return defense_groups
            
        except Exception as e:
            logger.error(f"Error calculating defense stats: {e}")
            return pd.DataFrame()
    
    def get_defensive_rankings(self, position: Optional[str] = None) -> pd.DataFrame:
        """Get defensive rankings by position"""
        logger.info(f"📊 Getting defensive rankings for position: {position or 'All'}")
        
        try:
            defense_stats = self.get_team_defense_stats()
            if defense_stats.empty:
                return pd.DataFrame()
            
            # Filter by position if specified
            if position:
                defense_stats = defense_stats[defense_stats['position'] == position]
            
            # Rank teams by fantasy points allowed (lower is better)
            defense_stats['defensive_rank'] = defense_stats['fantasy_points_allowed'].rank(ascending=True)
            
            # Sort by rank
            defense_stats = defense_stats.sort_values('defensive_rank')
            
            logger.info(f"✅ Defensive rankings calculated for {len(defense_stats)} teams")
            return defense_stats
            
        except Exception as e:
            logger.error(f"Error getting defensive rankings: {e}")
            return pd.DataFrame()
    
    def get_matchup_advantages(self, player_id: int, opponent_team_id: int) -> Dict[str, float]:
        """Get matchup advantages for a specific player against a team"""
        logger.info(f"🎯 Analyzing matchup advantage for player {player_id} vs team {opponent_team_id}")
        
        try:
            # Get player data
            players = db.get_players()
            player_data = players[players['id'] == player_id]
            
            if player_data.empty:
                logger.warning(f"Player {player_id} not found")
                return {}
            
            player_position = player_data['primary_position'].iloc[0]
            position_category = self.position_mapping.get(player_position, 'Unknown')
            
            # Get team defense stats
            defense_stats = self.get_team_defense_stats()
            team_defense = defense_stats[
                (defense_stats['team_id'] == opponent_team_id) & 
                (defense_stats['position'] == position_category)
            ]
            
            if team_defense.empty:
                logger.warning(f"No defense stats found for team {opponent_team_id} vs {position_category}")
                return {}
            
            # Calculate advantages
            defense_row = team_defense.iloc[0]
            
            advantages = {
                'fantasy_points_advantage': 50 - defense_row['fantasy_points_allowed'],  # vs league average
                'points_advantage': 25 - defense_row['points_allowed'],
                'rebounds_advantage': 10 - defense_row['rebounds_allowed'],
                'assists_advantage': 5 - defense_row['assists_allowed'],
                'defensive_rating': defense_row['defensive_rating'],
                'games_analyzed': defense_row['games_played']
            }
            
            logger.info(f"✅ Matchup advantages calculated: {advantages}")
            return advantages
            
        except Exception as e:
            logger.error(f"Error calculating matchup advantages: {e}")
            return {}
    
    def get_position_defense_summary(self) -> pd.DataFrame:
        """Get summary of defensive performance by position"""
        logger.info("📊 Generating position defense summary...")
        
        try:
            defense_stats = self.get_team_defense_stats()
            if defense_stats.empty:
                return pd.DataFrame()
            
            # Group by position and calculate league averages
            position_summary = defense_stats.groupby('position').agg({
                'fantasy_points_allowed': ['mean', 'std', 'min', 'max'],
                'defensive_rating': ['mean', 'std'],
                'games_played': 'sum'
            }).reset_index()
            
            # Flatten column names
            position_summary.columns = ['position', 'avg_fantasy_points_allowed', 'std_fantasy_points_allowed',
                                      'min_fantasy_points_allowed', 'max_fantasy_points_allowed',
                                      'avg_defensive_rating', 'std_defensive_rating', 'total_games']
            
            logger.info(f"✅ Position defense summary generated for {len(position_summary)} positions")
            return position_summary
            
        except Exception as e:
            logger.error(f"Error generating position defense summary: {e}")
            return pd.DataFrame()

def analyze_team_defense(season: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Main function to analyze team defense"""
    analyzer = TeamDefenseAnalyzer()
    
    results = {
        'defense_stats': analyzer.get_team_defense_stats(season),
        'rankings': analyzer.get_defensive_rankings(),
        'position_summary': analyzer.get_position_defense_summary()
    }
    
    return results

if __name__ == "__main__":
    # Example usage
    results = analyze_team_defense()
    
    print("Team Defense Analysis Results:")
    print(f"Defense stats shape: {results['defense_stats'].shape}")
    print(f"Rankings shape: {results['rankings'].shape}")
    print(f"Position summary shape: {results['position_summary'].shape}")

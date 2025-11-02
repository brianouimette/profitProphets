"""
Injury Impact Analysis
Analyzes injury impact and identifies replacement players
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from ml_service.database import db
from ml_service.config import config

logger = logging.getLogger(__name__)

class InjuryImpactAnalyzer:
    """Analyzes injury impact and finds replacement players"""
    
    def __init__(self):
        """Initialize the injury impact analyzer"""
        pass
    
    def analyze_injury_impact(self, player_id: int) -> Dict:
        """
        Analyze the impact of an injured player and find replacements
        
        Args:
            player_id: ID of the injured player
        
        Returns:
            Dictionary with injury impact analysis
        """
        logger.info(f"🏥 Analyzing injury impact for player {player_id}")
        
        try:
            # Get injury details
            injuries = db.get_player_injuries()
            player_injury = injuries[injuries['player_id'] == player_id]
            
            if player_injury.empty:
                return {'error': 'No active injury found for player'}
            
            injury = player_injury.iloc[0]
            
            # Get player details
            players = db.get_players()
            player = players[players['id'] == player_id]
            
            if player.empty:
                return {'error': 'Player not found'}
            
            player_info = player.iloc[0]
            
            # Get player's recent performance
            recent_performance = self._get_player_performance(player_id)
            
            # Find replacement players
            replacements = self._find_replacement_players(
                position=player_info['primary_position'],
                team_id=player_info.get('current_team_id'),
                exclude_player_id=player_id,
                min_games=5
            )
            
            # Calculate impact
            impact = self._calculate_impact(recent_performance, replacements)
            
            # Get team context
            team_context = self._get_team_context(player_info.get('current_team_id'))
            
            return {
                'injured_player': {
                    'id': player_id,
                    'name': f"{player_info['first_name']} {player_info['last_name']}",
                    'position': player_info['primary_position'],
                    'team_id': player_info.get('current_team_id'),
                    'injury_type': injury.get('injury_type'),
                    'status': injury.get('status'),
                    'start_date': injury.get('start_date'),
                    'expected_return': injury.get('expected_return')
                },
                'recent_performance': recent_performance,
                'replacement_options': replacements.to_dict('records') if not replacements.empty else [],
                'impact_analysis': impact,
                'team_context': team_context
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing injury impact: {e}")
            return {'error': str(e)}
    
    def get_all_active_injuries_impact(self) -> pd.DataFrame:
        """
        Get impact analysis for all active injuries
        
        Returns:
            DataFrame with injury impacts
        """
        logger.info("🏥 Analyzing all active injuries")
        
        try:
            injuries = db.get_player_injuries()
            active_injuries = injuries[injuries['status'].isin(['OUT', 'QUESTIONABLE', 'DOUBTFUL'])]
            
            if active_injuries.empty:
                return pd.DataFrame()
            
            impact_list = []
            for _, injury in active_injuries.iterrows():
                analysis = self.analyze_injury_impact(injury['player_id'])
                if 'error' not in analysis:
                    impact_list.append({
                        'player_id': analysis['injured_player']['id'],
                        'player_name': analysis['injured_player']['name'],
                        'position': analysis['injured_player']['position'],
                        'impact_level': analysis['impact_analysis'].get('impact_level', 'UNKNOWN'),
                        'performance_gap': analysis['impact_analysis'].get('performance_gap', 0),
                        'best_replacement': analysis['impact_analysis'].get('best_replacement_name', 'None'),
                        'replacement_count': len(analysis.get('replacement_options', []))
                    })
            
            return pd.DataFrame(impact_list)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing all injuries: {e}")
            return pd.DataFrame()
    
    def _get_player_performance(self, player_id: int, days: int = 30) -> Dict:
        """Get recent performance metrics for a player"""
        try:
            game_logs = db.get_player_game_logs()
            games = db.get_games()
            
            # Get recent game logs
            recent_logs = game_logs[game_logs['player_id'] == player_id]
            
            if recent_logs.empty:
                return {
                    'avg_fantasy_points': 0,
                    'consistency': 0,
                    'games_played': 0,
                    'trend': 'unknown'
                }
            
            # Merge with games to filter by date if needed
            recent_logs = recent_logs.merge(
                games[['id', 'game_date']],
                left_on='game_id',
                right_on='id',
                how='left'
            )
            
            # Calculate stats
            avg_fp = recent_logs['fantasy_points'].mean()
            std_fp = recent_logs['fantasy_points'].std()
            games_count = len(recent_logs)
            
            # Calculate trend (last 5 games vs previous 5)
            if games_count >= 10:
                sorted_logs = recent_logs.sort_values('game_date')
                recent_5 = sorted_logs.tail(5)['fantasy_points'].mean()
                previous_5 = sorted_logs.iloc[-10:-5]['fantasy_points'].mean()
                trend = 'improving' if recent_5 > previous_5 else 'declining'
            else:
                trend = 'insufficient_data'
            
            return {
                'avg_fantasy_points': float(avg_fp) if not pd.isna(avg_fp) else 0,
                'consistency': float(std_fp) if not pd.isna(std_fp) else 0,
                'games_played': int(games_count),
                'trend': trend
            }
            
        except Exception as e:
            logger.error(f"Error getting player performance: {e}")
            return {'avg_fantasy_points': 0, 'consistency': 0, 'games_played': 0, 'trend': 'unknown'}
    
    def _find_replacement_players(
        self, 
        position: str, 
        team_id: Optional[int] = None,
        exclude_player_id: Optional[int] = None,
        min_games: int = 5
    ) -> pd.DataFrame:
        """
        Find replacement players for a given position
        
        Args:
            position: Position to find replacements for
            team_id: Optional team filter (same team replacements)
            exclude_player_id: Player ID to exclude
            min_games: Minimum games played requirement
        
        Returns:
            DataFrame with replacement options
        """
        try:
            players = db.get_players()
            game_logs = db.get_player_game_logs()
            injuries = db.get_player_injuries()
            teams = db.get_teams()
            
            # Filter by position
            candidates = players[players['primary_position'] == position]
            
            # Exclude injured player
            if exclude_player_id:
                candidates = candidates[candidates['id'] != exclude_player_id]
            
            # Exclude other injured players
            active_injuries = injuries[injuries['status'].isin(['OUT', 'QUESTIONABLE'])]
            if not active_injuries.empty:
                candidates = candidates[~candidates['id'].isin(active_injuries['player_id'])]
            
            # Optional: Filter by team (same team replacements)
            if team_id:
                candidates = candidates[candidates['current_team_id'] == team_id]
            
            if candidates.empty:
                return pd.DataFrame()
            
            # Get performance stats
            candidate_logs = game_logs[game_logs['player_id'].isin(candidates['id'])]
            
            if candidate_logs.empty:
                return pd.DataFrame()
            
            # Calculate performance metrics
            performance = candidate_logs.groupby('player_id').agg({
                'fantasy_points': ['mean', 'std', 'count'],
                'rebounds': 'mean',
                'assists': 'mean',
                'steals': 'mean',
                'blocks': 'mean'
            }).reset_index()
            
            performance.columns = [
                'player_id', 'avg_fantasy_points', 'consistency', 'games_played',
                'avg_rebounds', 'avg_assists', 'avg_steals', 'avg_blocks'
            ]
            
            # Filter by minimum games
            performance = performance[performance['games_played'] >= min_games]
            
            if performance.empty:
                return pd.DataFrame()
            
            # Merge with player and team info
            replacements = performance.merge(
                candidates[['id', 'first_name', 'last_name', 'primary_position', 'current_team_id']],
                left_on='player_id',
                right_on='id',
                how='left'
            )
            
            replacements = replacements.merge(
                teams[['id', 'abbreviation', 'city', 'name']],
                left_on='current_team_id',
                right_on='id',
                how='left',
                suffixes=('', '_team')
            )
            
            # Calculate replacement score (combination of performance and consistency)
            replacements['replacement_score'] = (
                replacements['avg_fantasy_points'] * 0.7 +
                (50 - replacements['consistency'].fillna(25)) * 0.3
            )
            
            # Sort by replacement score
            replacements = replacements.sort_values('replacement_score', ascending=False)
            
            return replacements.head(20)
            
        except Exception as e:
            logger.error(f"Error finding replacement players: {e}")
            return pd.DataFrame()
    
    def _calculate_impact(self, player_performance: Dict, replacements: pd.DataFrame) -> Dict:
        """Calculate the impact of losing the player"""
        try:
            if replacements.empty:
                return {
                    'impact_level': 'HIGH',
                    'reason': 'No suitable replacements found',
                    'performance_gap': player_performance.get('avg_fantasy_points', 0),
                    'best_replacement_name': None,
                    'best_replacement_avg': None
                }
            
            player_avg = player_performance.get('avg_fantasy_points', 0)
            best_replacement = replacements.iloc[0]
            replacement_avg = best_replacement['avg_fantasy_points']
            
            performance_gap = player_avg - replacement_avg
            
            # Determine impact level
            if performance_gap > 5:
                impact_level = 'HIGH'
            elif performance_gap > 2:
                impact_level = 'MEDIUM'
            elif performance_gap > 0:
                impact_level = 'LOW'
            else:
                impact_level = 'NEGLIGIBLE'  # Replacement might be better
            
            return {
                'impact_level': impact_level,
                'performance_gap': float(performance_gap),
                'best_replacement_name': f"{best_replacement['first_name']} {best_replacement['last_name']}",
                'best_replacement_avg': float(replacement_avg),
                'replacement_team': best_replacement.get('abbreviation', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error calculating impact: {e}")
            return {'impact_level': 'UNKNOWN', 'error': str(e)}
    
    def _get_team_context(self, team_id: Optional[int]) -> Dict:
        """Get team context for injury impact"""
        try:
            if not team_id:
                return {}
            
            teams = db.get_teams()
            team = teams[teams['id'] == team_id]
            
            if team.empty:
                return {}
            
            team_info = team.iloc[0]
            
            # Could add more team-specific analysis here
            return {
                'team_name': team_info.get('name'),
                'team_abbreviation': team_info.get('abbreviation')
            }
            
        except Exception as e:
            logger.error(f"Error getting team context: {e}")
            return {}

def analyze_injury_impact(player_id: int) -> Dict:
    """Main function to analyze injury impact"""
    analyzer = InjuryImpactAnalyzer()
    return analyzer.analyze_injury_impact(player_id)

if __name__ == "__main__":
    # Example usage
    impact = analyze_injury_impact(12345)
    print("Injury Impact Analysis:")
    print(impact)


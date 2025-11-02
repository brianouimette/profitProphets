"""
Salary Value Analysis
Analyzes players for value identification within salary tiers
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from ml_service.database import db
from ml_service.config import config

logger = logging.getLogger(__name__)

class ValueAnalyzer:
    """Analyzes salary-based value for daily fantasy players"""
    
    def __init__(self):
        """Initialize the value analyzer"""
        self.salary_tiers = {
            'elite': (10000, float('inf')),
            'high': (7500, 9999),
            'mid': (5000, 7499),
            'low': (3000, 4999),
            'minimum': (0, 2999)
        }
    
    def get_value_analysis(self, game_date: str, season: Optional[str] = None) -> pd.DataFrame:
        """
        Analyze salary-based value for all players on a given date
        
        Args:
            game_date: Date to analyze (YYYY-MM-DD format)
            season: Optional season filter
        
        Returns:
            DataFrame with value analysis
        """
        logger.info(f"💰 Analyzing value for date: {game_date}")
        
        try:
            # Get DFS projections for the date
            projections = self._get_dfs_projections_for_date(game_date)
            if projections.empty:
                logger.warning(f"No DFS projections found for {game_date}")
                return pd.DataFrame()
            
            # Get recent player performance
            recent_performance = self._get_recent_performance(projections['player_id'].unique(), game_date)
            
            # Get team defense stats
            defense_stats = self._get_team_defense_context(projections, game_date)
            
            # Merge all data
            analysis = projections.merge(recent_performance, on='player_id', how='left')
            analysis = analysis.merge(defense_stats, on=['player_id', 'game_id'], how='left')
            
            # Calculate value metrics
            analysis['value_per_dollar'] = analysis['projected_fantasy_points'] / analysis['salary'] * 1000
            analysis['ceiling_value'] = analysis['ceiling'] / analysis['salary'] * 1000
            analysis['floor_value'] = analysis['floor'] / analysis['salary'] * 1000
            analysis['value_score'] = self._calculate_value_score(analysis)
            analysis['salary_tier'] = analysis['salary'].apply(self._get_salary_tier)
            
            # Add value rank within salary tier
            analysis['tier_value_rank'] = analysis.groupby('salary_tier')['value_score'].rank(ascending=False)
            
            # Calculate value vs expectation
            if 'recent_avg_fantasy_points' in analysis.columns:
                analysis['value_vs_expectation'] = (
                    analysis['value_per_dollar'] - 
                    (analysis['recent_avg_fantasy_points'] / analysis['salary'] * 1000)
                )
            
            # Sort by value score
            analysis = analysis.sort_values('value_score', ascending=False)
            
            logger.info(f"✅ Value analysis completed: {len(analysis)} players analyzed")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in value analysis: {e}")
            return pd.DataFrame()
    
    def get_tier_value_rankings(self, game_date: str, tier: Optional[str] = None) -> pd.DataFrame:
        """
        Get value rankings by salary tier
        
        Args:
            game_date: Date to analyze
            tier: Optional tier filter ('elite', 'high', 'mid', 'low', 'minimum')
        
        Returns:
            DataFrame with tier rankings
        """
        logger.info(f"📊 Getting tier value rankings for {tier or 'all tiers'}")
        
        try:
            analysis = self.get_value_analysis(game_date)
            if analysis.empty:
                return pd.DataFrame()
            
            if tier:
                if tier not in self.salary_tiers:
                    logger.warning(f"Invalid tier: {tier}")
                    return pd.DataFrame()
                analysis = analysis[analysis['salary_tier'] == tier]
            
            # Sort by tier value rank
            analysis = analysis.sort_values(['salary_tier', 'tier_value_rank'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error getting tier rankings: {e}")
            return pd.DataFrame()
    
    def get_best_values(self, game_date: str, limit: int = 20) -> pd.DataFrame:
        """
        Get the best value players across all tiers
        
        Args:
            game_date: Date to analyze
            limit: Number of players to return
        
        Returns:
            DataFrame with top value players
        """
        logger.info(f"⭐ Finding best value players for {game_date}")
        
        try:
            analysis = self.get_value_analysis(game_date)
            if analysis.empty:
                return pd.DataFrame()
            
            # Get top value players, ensuring diversity across tiers
            top_players = []
            players_per_tier = max(1, limit // len(self.salary_tiers))
            
            for tier in ['elite', 'high', 'mid', 'low', 'minimum']:
                tier_players = analysis[analysis['salary_tier'] == tier].head(players_per_tier)
                top_players.append(tier_players)
            
            result = pd.concat(top_players).head(limit)
            result = result.sort_values('value_score', ascending=False)
            
            logger.info(f"✅ Found {len(result)} best value players")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error finding best values: {e}")
            return pd.DataFrame()
    
    def _get_dfs_projections_for_date(self, game_date: str) -> pd.DataFrame:
        """Get DFS projections for a specific date"""
        try:
            # Get games for the date
            games = db.get_games()
            games = games[games['game_date'] == game_date]
            
            if games.empty:
                return pd.DataFrame()
            
            # Get projections
            projections = db.get_dfs_projections()
            projections = projections[projections['game_id'].isin(games['id'])]
            
            # Merge with player and game info
            players = db.get_players()
            projections = projections.merge(
                players[['id', 'first_name', 'last_name', 'primary_position', 'current_team_id']],
                left_on='player_id',
                right_on='id',
                how='left',
                suffixes=('', '_player')
            )
            
            projections = projections.merge(
                games[['id', 'home_team_id', 'away_team_id']],
                left_on='game_id',
                right_on='id',
                how='left',
                suffixes=('', '_game')
            )
            
            return projections
            
        except Exception as e:
            logger.error(f"Error getting DFS projections: {e}")
            return pd.DataFrame()
    
    def _get_recent_performance(self, player_ids: List[int], game_date: str, days: int = 30) -> pd.DataFrame:
        """Get recent performance for players"""
        try:
            game_logs = db.get_player_game_logs()
            games = db.get_games()
            
            # Filter to recent games
            cutoff_date = pd.to_datetime(game_date) - pd.Timedelta(days=days)
            games_recent = games[pd.to_datetime(games['game_date']) >= cutoff_date]
            
            if games_recent.empty:
                return pd.DataFrame(columns=['player_id', 'recent_avg_fantasy_points', 'recent_consistency'])
            
            # Filter game logs
            recent_logs = game_logs[
                (game_logs['player_id'].isin(player_ids)) &
                (game_logs['game_id'].isin(games_recent['id']))
            ]
            
            if recent_logs.empty:
                return pd.DataFrame(columns=['player_id', 'recent_avg_fantasy_points', 'recent_consistency'])
            
            # Calculate stats
            performance = recent_logs.groupby('player_id').agg({
                'fantasy_points': ['mean', 'std', 'count']
            }).reset_index()
            
            performance.columns = ['player_id', 'recent_avg_fantasy_points', 'recent_std', 'recent_games']
            performance['recent_consistency'] = performance['recent_std'].fillna(0)
            
            return performance[['player_id', 'recent_avg_fantasy_points', 'recent_consistency']]
            
        except Exception as e:
            logger.error(f"Error getting recent performance: {e}")
            return pd.DataFrame()
    
    def _get_team_defense_context(self, projections: pd.DataFrame, game_date: str) -> pd.DataFrame:
        """Get team defense context for matchups"""
        try:
            # This would integrate with team defense analyzer
            # For now, return empty DataFrame with expected columns
            return pd.DataFrame(columns=['player_id', 'game_id', 'defense_advantage'])
            
        except Exception as e:
            logger.error(f"Error getting defense context: {e}")
            return pd.DataFrame()
    
    def _calculate_value_score(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate composite value score
        
        Factors:
        - Value per dollar (projected points / salary)
        - Consistency (lower std dev is better)
        - Ceiling potential
        - Recent performance trend
        """
        # Base value score
        value_score = df['value_per_dollar'].fillna(0)
        
        # Adjust for ceiling (potential upside)
        if 'ceiling_value' in df.columns:
            value_score += (df['ceiling_value'] - df['value_per_dollar']) * 0.2
        
        # Adjust for consistency (lower std = higher score)
        if 'recent_consistency' in df.columns:
            consistency_bonus = (1 - (df['recent_consistency'] / df['recent_avg_fantasy_points']).fillna(0)).clip(0, 1) * 0.5
            value_score += consistency_bonus
        
        # Adjust for ownership (lower ownership in good value = better contrarian play)
        if 'ownership_percentage' in df.columns:
            ownership_adjustment = (1 - df['ownership_percentage'] / 100).fillna(0.5) * 0.3
            value_score += ownership_adjustment
        
        return value_score
    
    def _get_salary_tier(self, salary: float) -> str:
        """Determine salary tier for a player"""
        for tier_name, (min_salary, max_salary) in self.salary_tiers.items():
            if min_salary <= salary <= max_salary:
                return tier_name
        return 'unknown'

def analyze_value(game_date: str) -> Dict[str, pd.DataFrame]:
    """Main function to analyze value"""
    analyzer = ValueAnalyzer()
    
    results = {
        'all_players': analyzer.get_value_analysis(game_date),
        'by_tier': {},
        'best_values': analyzer.get_best_values(game_date)
    }
    
    for tier in ['elite', 'high', 'mid', 'low', 'minimum']:
        results['by_tier'][tier] = analyzer.get_tier_value_rankings(game_date, tier)
    
    return results

if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    results = analyze_value(today)
    print(f"Value Analysis Results:")
    print(f"All players: {len(results['all_players'])}")
    print(f"Best values: {len(results['best_values'])}")


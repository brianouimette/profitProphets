"""
Simulation Engine for NBA Fantasy Analysis
Monte Carlo simulation and scenario analysis for lineup optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from scipy import stats
from scipy.stats import norm, lognorm, gamma
import joblib
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SimulationType(Enum):
    MONTE_CARLO = "monte_carlo"
    SCENARIO = "scenario"
    BOOTSTRAP = "bootstrap"

@dataclass
class SimulationResult:
    mean_score: float
    std_score: float
    percentile_10: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_90: float
    confidence_interval_95: Tuple[float, float]
    probability_above_threshold: float
    iterations: int
    simulation_type: SimulationType

@dataclass
class PlayerProjection:
    player_id: int
    name: str
    position: str
    salary: float
    mean_projection: float
    std_projection: float
    distribution_type: str
    correlation_factors: Dict[str, float]

class PerformanceDistribution:
    """Model player performance as probability distributions"""
    
    def __init__(self):
        self.distributions = {}
        self.fitted_params = {}
    
    def fit_distribution(self, data: pd.Series, distribution_type: str = 'auto') -> Dict[str, Any]:
        """Fit probability distribution to player performance data"""
        try:
            if distribution_type == 'auto':
                # Test multiple distributions and select best fit
                distributions = ['normal', 'lognormal', 'gamma', 'beta']
                best_fit = None
                best_ks_stat = float('inf')
                
                for dist_name in distributions:
                    try:
                        if dist_name == 'normal':
                            params = stats.norm.fit(data)
                            ks_stat, _ = stats.kstest(data, lambda x: stats.norm.cdf(x, *params))
                        elif dist_name == 'lognormal':
                            params = stats.lognorm.fit(data)
                            ks_stat, _ = stats.kstest(data, lambda x: stats.lognorm.cdf(x, *params))
                        elif dist_name == 'gamma':
                            params = stats.gamma.fit(data)
                            ks_stat, _ = stats.kstest(data, lambda x: stats.gamma.cdf(x, *params))
                        elif dist_name == 'beta':
                            # Scale data to [0,1] for beta distribution
                            scaled_data = (data - data.min()) / (data.max() - data.min())
                            params = stats.beta.fit(scaled_data)
                            ks_stat, _ = stats.kstest(scaled_data, lambda x: stats.beta.cdf(x, *params))
                        
                        if ks_stat < best_ks_stat:
                            best_ks_stat = ks_stat
                            best_fit = (dist_name, params)
                    except:
                        continue
                
                if best_fit:
                    distribution_type, params = best_fit
                else:
                    distribution_type, params = 'normal', stats.norm.fit(data)
            
            elif distribution_type == 'normal':
                params = stats.norm.fit(data)
            elif distribution_type == 'lognormal':
                params = stats.lognorm.fit(data)
            elif distribution_type == 'gamma':
                params = stats.gamma.fit(data)
            else:
                params = stats.norm.fit(data)
            
            return {
                'distribution_type': distribution_type,
                'parameters': params,
                'mean': np.mean(data),
                'std': np.std(data),
                'ks_statistic': best_ks_stat if distribution_type == 'auto' else None
            }
            
        except Exception as e:
            logger.error(f"Error fitting distribution: {e}")
            return {
                'distribution_type': 'normal',
                'parameters': (np.mean(data), np.std(data)),
                'mean': np.mean(data),
                'std': np.std(data),
                'ks_statistic': None
            }
    
    def sample_from_distribution(self, distribution_info: Dict[str, Any], n_samples: int) -> np.ndarray:
        """Sample from fitted distribution"""
        dist_type = distribution_info['distribution_type']
        params = distribution_info['parameters']
        
        try:
            if dist_type == 'normal':
                return np.random.normal(params[0], params[1], n_samples)
            elif dist_type == 'lognormal':
                return np.random.lognormal(params[0], params[1], n_samples)
            elif dist_type == 'gamma':
                return np.random.gamma(params[0], params[1], n_samples)
            elif dist_type == 'beta':
                return np.random.beta(params[0], params[1], n_samples)
            else:
                return np.random.normal(params[0], params[1], n_samples)
        except Exception as e:
            logger.error(f"Error sampling from distribution: {e}")
            return np.random.normal(params[0], params[1], n_samples)

class CorrelationMatrix:
    """Calculate and model correlations between players"""
    
    def __init__(self):
        self.correlation_matrix = None
        self.cholesky_matrix = None
    
    def calculate_correlations(self, player_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix between players"""
        try:
            # Pivot data to have players as columns and games as rows
            pivot_data = player_data.pivot_table(
                index='game_id', 
                columns='player_id', 
                values='fantasy_points', 
                fill_value=0
            )
            
            # Calculate correlation matrix
            self.correlation_matrix = pivot_data.corr()
            
            # Ensure positive definiteness for Cholesky decomposition
            self._ensure_positive_definite()
            
            return self.correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            return pd.DataFrame()
    
    def _ensure_positive_definite(self):
        """Ensure correlation matrix is positive definite"""
        try:
            # Add small value to diagonal if needed
            min_eigenval = np.min(np.real(np.linalg.eigvals(self.correlation_matrix)))
            if min_eigenval < 1e-8:
                self.correlation_matrix += np.eye(len(self.correlation_matrix)) * (1e-8 - min_eigenval)
            
            # Calculate Cholesky decomposition
            self.cholesky_matrix = np.linalg.cholesky(self.correlation_matrix)
        except Exception as e:
            logger.error(f"Error ensuring positive definiteness: {e}")
            self.cholesky_matrix = np.eye(len(self.correlation_matrix))
    
    def generate_correlated_samples(self, independent_samples: np.ndarray) -> np.ndarray:
        """Generate correlated samples using Cholesky decomposition"""
        try:
            if self.cholesky_matrix is None:
                return independent_samples
            
            return np.dot(independent_samples, self.cholesky_matrix.T)
        except Exception as e:
            logger.error(f"Error generating correlated samples: {e}")
            return independent_samples

class ScenarioBuilder:
    """Build different what-if scenarios"""
    
    def __init__(self):
        self.scenarios = {}
    
    def create_injury_scenario(self, injured_player_id: int, replacement_player_id: int) -> Dict[str, Any]:
        """Create scenario with injured player replaced"""
        return {
            'type': 'injury',
            'injured_player_id': injured_player_id,
            'replacement_player_id': replacement_player_id,
            'impact_factor': 0.8,  # Replacement typically 80% of original
            'variance_adjustment': 1.2  # Higher variance for replacement
        }
    
    def create_weather_scenario(self, venue: str, weather_impact: float) -> Dict[str, Any]:
        """Create weather impact scenario"""
        return {
            'type': 'weather',
            'venue': venue,
            'impact_factor': weather_impact,
            'affected_positions': ['all'],
            'variance_adjustment': 1.1
        }
    
    def create_rest_scenario(self, player_ids: List[int], rest_impact: float) -> Dict[str, Any]:
        """Create rest day impact scenario"""
        return {
            'type': 'rest',
            'player_ids': player_ids,
            'impact_factor': rest_impact,
            'variance_adjustment': 0.9
        }
    
    def create_matchup_scenario(self, player_id: int, opponent_strength: float) -> Dict[str, Any]:
        """Create matchup difficulty scenario"""
        return {
            'type': 'matchup',
            'player_id': player_id,
            'opponent_strength': opponent_strength,
            'impact_factor': opponent_strength,
            'variance_adjustment': 1.0
        }

class SimulationEngine:
    """Main simulation engine for NBA fantasy analysis"""
    
    def __init__(self, database, model_cache_dir='./ml_models'):
        self.db = database
        self.model_cache_dir = model_cache_dir
        self.performance_dist = PerformanceDistribution()
        self.correlation_matrix = CorrelationMatrix()
        self.scenario_builder = ScenarioBuilder()
        
        # Create model cache directory
        os.makedirs(self.model_cache_dir, exist_ok=True)
    
    def monte_carlo_simulation(
        self, 
        lineup: List[PlayerProjection], 
        iterations: int = 10000,
        game_date: Optional[str] = None,
        include_correlations: bool = True
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation for lineup outcomes
        
        Args:
            lineup: List of player projections
            iterations: Number of simulation iterations
            game_date: Game date for context
            include_correlations: Whether to include player correlations
        
        Returns:
            SimulationResult with comprehensive statistics
        """
        logger.info(f"🎲 Running Monte Carlo simulation with {iterations} iterations")
        
        try:
            # Get historical data for correlation analysis
            if include_correlations:
                historical_data = self._get_historical_correlation_data(lineup, game_date)
                if not historical_data.empty:
                    self.correlation_matrix.calculate_correlations(historical_data)
            
            # Generate independent samples for each player
            independent_samples = np.random.normal(0, 1, (iterations, len(lineup)))
            
            # Apply correlations if available
            if include_correlations and self.correlation_matrix.cholesky_matrix is not None:
                correlated_samples = self.correlation_matrix.generate_correlated_samples(independent_samples)
            else:
                correlated_samples = independent_samples
            
            # Generate lineup scores
            lineup_scores = []
            
            for i in range(iterations):
                iteration_score = 0
                
                for j, player in enumerate(lineup):
                    # Sample from player's distribution
                    if player.distribution_type == 'normal':
                        sample = np.random.normal(player.mean_projection, player.std_projection)
                    elif player.distribution_type == 'lognormal':
                        sample = np.random.lognormal(player.mean_projection, player.std_projection)
                    else:
                        sample = np.random.normal(player.mean_projection, player.std_projection)
                    
                    # Apply correlation adjustment
                    if include_correlations:
                        correlation_factor = correlated_samples[i, j]
                        sample = sample * (1 + correlation_factor * 0.1)  # 10% correlation impact
                    
                    iteration_score += max(0, sample)  # Ensure non-negative
                
                lineup_scores.append(iteration_score)
            
            lineup_scores = np.array(lineup_scores)
            
            # Calculate statistics
            mean_score = np.mean(lineup_scores)
            std_score = np.std(lineup_scores)
            
            percentiles = np.percentile(lineup_scores, [10, 25, 50, 75, 90])
            
            # Confidence interval
            ci_95 = np.percentile(lineup_scores, [2.5, 97.5])
            
            # Probability above threshold (e.g., 300 points)
            threshold = 300
            prob_above_threshold = np.mean(lineup_scores > threshold)
            
            result = SimulationResult(
                mean_score=float(mean_score),
                std_score=float(std_score),
                percentile_10=float(percentiles[0]),
                percentile_25=float(percentiles[1]),
                percentile_50=float(percentiles[2]),
                percentile_75=float(percentiles[3]),
                percentile_90=float(percentiles[4]),
                confidence_interval_95=(float(ci_95[0]), float(ci_95[1])),
                probability_above_threshold=float(prob_above_threshold),
                iterations=iterations,
                simulation_type=SimulationType.MONTE_CARLO
            )
            
            logger.info(f"✅ Monte Carlo simulation completed: Mean={mean_score:.2f}, Std={std_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Monte Carlo simulation: {e}")
            return SimulationResult(
                mean_score=0, std_score=0, percentile_10=0, percentile_25=0,
                percentile_50=0, percentile_75=0, percentile_90=0,
                confidence_interval_95=(0, 0), probability_above_threshold=0,
                iterations=0, simulation_type=SimulationType.MONTE_CARLO
            )
    
    def scenario_analysis(
        self, 
        base_lineup: List[PlayerProjection], 
        scenarios: List[Dict[str, Any]],
        iterations: int = 5000
    ) -> Dict[str, SimulationResult]:
        """
        What-if analysis for different scenarios
        
        Args:
            base_lineup: Base lineup projections
            scenarios: List of scenario definitions
            iterations: Number of iterations per scenario
        
        Returns:
            Dictionary of scenario results
        """
        logger.info(f"📊 Running scenario analysis with {len(scenarios)} scenarios")
        
        results = {}
        
        for i, scenario in enumerate(scenarios):
            logger.info(f"Analyzing scenario {i+1}: {scenario.get('type', 'unknown')}")
            
            # Adjust lineup based on scenario
            adjusted_lineup = self._apply_scenario_to_lineup(base_lineup, scenario)
            
            # Run simulation for adjusted lineup
            scenario_result = self.monte_carlo_simulation(
                adjusted_lineup, 
                iterations, 
                include_correlations=True
            )
            
            results[f"scenario_{i+1}_{scenario.get('type', 'unknown')}"] = scenario_result
        
        return results
    
    def variance_modeling(
        self, 
        player_data: pd.DataFrame, 
        historical_games: int = 50
    ) -> Dict[int, Dict[str, Any]]:
        """
        Statistical variance modeling for player performance
        
        Args:
            player_data: Historical player performance data
            historical_games: Number of recent games to analyze
        
        Returns:
            Dictionary of variance models for each player
        """
        logger.info(f"📈 Building variance models for {len(player_data['player_id'].unique())} players")
        
        variance_models = {}
        
        for player_id in player_data['player_id'].unique():
            try:
                player_games = player_data[player_data['player_id'] == player_id].tail(historical_games)
                
                if len(player_games) < 10:  # Need minimum games for analysis
                    continue
                
                # Calculate variance components
                fantasy_points = player_games['fantasy_points'].values
                
                # Base variance
                base_variance = np.var(fantasy_points)
                
                # Trend-adjusted variance
                if len(fantasy_points) > 5:
                    trend = np.polyfit(range(len(fantasy_points)), fantasy_points, 1)[0]
                    trend_adjusted_variance = np.var(fantasy_points - np.arange(len(fantasy_points)) * trend)
                else:
                    trend_adjusted_variance = base_variance
                
                # Matchup-specific variance
                matchup_variance = self._calculate_matchup_variance(player_games)
                
                # Rest day variance
                rest_variance = self._calculate_rest_variance(player_games)
                
                variance_models[player_id] = {
                    'base_variance': float(base_variance),
                    'trend_adjusted_variance': float(trend_adjusted_variance),
                    'matchup_variance': float(matchup_variance),
                    'rest_variance': float(rest_variance),
                    'total_variance': float(base_variance + matchup_variance + rest_variance),
                    'variance_components': {
                        'base': float(base_variance),
                        'matchup': float(matchup_variance),
                        'rest': float(rest_variance)
                    }
                }
                
            except Exception as e:
                logger.error(f"Error modeling variance for player {player_id}: {e}")
                continue
        
        logger.info(f"✅ Variance modeling completed for {len(variance_models)} players")
        return variance_models
    
    def _get_historical_correlation_data(
        self, 
        lineup: List[PlayerProjection], 
        game_date: Optional[str]
    ) -> pd.DataFrame:
        """Get historical data for correlation analysis"""
        try:
            player_ids = [p.player_id for p in lineup]
            
            # Get recent games data
            query = """
            SELECT pgl.player_id, pgl.game_id, pgl.fantasy_points, g.game_date
            FROM player_game_logs pgl
            JOIN games g ON pgl.game_id = g.id
            WHERE pgl.player_id IN ({})
            AND g.game_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY g.game_date DESC
            """.format(','.join(map(str, player_ids)))
            
            return self.db.get_dataframe(query)
            
        except Exception as e:
            logger.error(f"Error getting historical correlation data: {e}")
            return pd.DataFrame()
    
    def _apply_scenario_to_lineup(
        self, 
        lineup: List[PlayerProjection], 
        scenario: Dict[str, Any]
    ) -> List[PlayerProjection]:
        """Apply scenario adjustments to lineup"""
        adjusted_lineup = lineup.copy()
        
        scenario_type = scenario.get('type', '')
        impact_factor = scenario.get('impact_factor', 1.0)
        variance_adjustment = scenario.get('variance_adjustment', 1.0)
        
        if scenario_type == 'injury':
            # Replace injured player
            injured_id = scenario.get('injured_player_id')
            replacement_id = scenario.get('replacement_player_id')
            
            for i, player in enumerate(adjusted_lineup):
                if player.player_id == injured_id:
                    # This would need to be replaced with actual replacement player data
                    adjusted_lineup[i].mean_projection *= impact_factor
                    adjusted_lineup[i].std_projection *= variance_adjustment
        
        elif scenario_type == 'weather':
            # Apply weather impact to all players
            for player in adjusted_lineup:
                player.mean_projection *= impact_factor
                player.std_projection *= variance_adjustment
        
        elif scenario_type == 'rest':
            # Apply rest impact to specific players
            affected_players = scenario.get('player_ids', [])
            for player in adjusted_lineup:
                if player.player_id in affected_players:
                    player.mean_projection *= impact_factor
                    player.std_projection *= variance_adjustment
        
        elif scenario_type == 'matchup':
            # Apply matchup impact to specific player
            affected_player = scenario.get('player_id')
            for player in adjusted_lineup:
                if player.player_id == affected_player:
                    player.mean_projection *= impact_factor
                    player.std_projection *= variance_adjustment
        
        return adjusted_lineup
    
    def _calculate_matchup_variance(self, player_games: pd.DataFrame) -> float:
        """Calculate matchup-specific variance"""
        try:
            if 'opponent_team_id' not in player_games.columns:
                return 0.0
            
            # Group by opponent and calculate variance within each matchup
            matchup_variances = []
            for opponent in player_games['opponent_team_id'].unique():
                opponent_games = player_games[player_games['opponent_team_id'] == opponent]
                if len(opponent_games) > 1:
                    matchup_variances.append(np.var(opponent_games['fantasy_points']))
            
            return np.mean(matchup_variances) if matchup_variances else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating matchup variance: {e}")
            return 0.0
    
    def _calculate_rest_variance(self, player_games: pd.DataFrame) -> float:
        """Calculate rest day variance"""
        try:
            if 'game_date' not in player_games.columns:
                return 0.0
            
            # Calculate days between games
            player_games['game_date'] = pd.to_datetime(player_games['game_date'])
            player_games = player_games.sort_values('game_date')
            
            rest_days = player_games['game_date'].diff().dt.days.fillna(0)
            
            # Group by rest days and calculate variance
            rest_variances = []
            for rest_day in rest_days.unique():
                if rest_day > 0:
                    rest_games = player_games[rest_days == rest_day]
                    if len(rest_games) > 1:
                        rest_variances.append(np.var(rest_games['fantasy_points']))
            
            return np.mean(rest_variances) if rest_variances else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating rest variance: {e}")
            return 0.0

def main():
    """Test the simulation engine"""
    logger.info("🧪 Testing Simulation Engine...")
    
    # Create mock database
    class MockDatabase:
        def get_dataframe(self, query):
            # Return mock data for testing
            return pd.DataFrame({
                'player_id': [1, 2, 3, 1, 2, 3],
                'game_id': [1, 1, 1, 2, 2, 2],
                'fantasy_points': [25.5, 18.2, 32.1, 28.3, 15.8, 29.7],
                'game_date': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-16', '2024-01-16', '2024-01-16']
            })
    
    # Initialize simulation engine
    engine = SimulationEngine(MockDatabase())
    
    # Create test lineup
    lineup = [
        PlayerProjection(
            player_id=1, name="Player 1", position="PG", salary=8000,
            mean_projection=25.0, std_projection=5.0, distribution_type="normal",
            correlation_factors={}
        ),
        PlayerProjection(
            player_id=2, name="Player 2", position="SG", salary=7500,
            mean_projection=20.0, std_projection=4.0, distribution_type="normal",
            correlation_factors={}
        ),
        PlayerProjection(
            player_id=3, name="Player 3", position="SF", salary=7000,
            mean_projection=18.0, std_projection=3.5, distribution_type="normal",
            correlation_factors={}
        )
    ]
    
    # Run Monte Carlo simulation
    result = engine.monte_carlo_simulation(lineup, iterations=1000)
    logger.info(f"Simulation result: Mean={result.mean_score:.2f}, Std={result.std_score:.2f}")
    
    # Test scenario analysis
    scenarios = [
        engine.scenario_builder.create_injury_scenario(1, 4),
        engine.scenario_builder.create_weather_scenario("Indoor", 0.95)
    ]
    
    scenario_results = engine.scenario_analysis(lineup, scenarios, iterations=500)
    logger.info(f"Scenario analysis completed: {len(scenario_results)} scenarios")

if __name__ == "__main__":
    main()

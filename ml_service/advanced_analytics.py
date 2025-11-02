"""
Advanced Statistical Analysis Engine
Comprehensive statistical modeling and analytics for NBA fantasy analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
from scipy import stats
from scipy.stats import norm, t, chi2
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class StatisticalModeler:
    """Advanced statistical modeling for NBA fantasy analysis"""
    
    def __init__(self):
        self.fitted_distributions = {}
        self.correlation_matrices = {}
        
    def fit_distributions(self, data: pd.Series, distributions: List[str] = None) -> Dict[str, Any]:
        """Fit various probability distributions to data"""
        if distributions is None:
            distributions = ['normal', 'lognormal', 'gamma', 'beta', 'exponential']
        
        logger.info(f"📊 Fitting {len(distributions)} distributions to data")
        
        results = {}
        
        for dist_name in distributions:
            try:
                if dist_name == 'normal':
                    params = stats.norm.fit(data)
                    ks_stat, p_value = stats.kstest(data, lambda x: stats.norm.cdf(x, *params))
                elif dist_name == 'lognormal':
                    params = stats.lognorm.fit(data)
                    ks_stat, p_value = stats.kstest(data, lambda x: stats.lognorm.cdf(x, *params))
                elif dist_name == 'gamma':
                    params = stats.gamma.fit(data)
                    ks_stat, p_value = stats.kstest(data, lambda x: stats.gamma.cdf(x, *params))
                elif dist_name == 'beta':
                    # Scale data to [0,1] for beta distribution
                    scaled_data = (data - data.min()) / (data.max() - data.min())
                    params = stats.beta.fit(scaled_data)
                    ks_stat, p_value = stats.kstest(scaled_data, lambda x: stats.beta.cdf(x, *params))
                elif dist_name == 'exponential':
                    params = stats.expon.fit(data)
                    ks_stat, p_value = stats.kstest(data, lambda x: stats.expon.cdf(x, *params))
                else:
                    continue
                
                # Calculate AIC and BIC
                n = len(data)
                k = len(params)
                
                # Calculate log-likelihood based on distribution type
                if dist_name == 'normal':
                    log_likelihood = np.sum(np.log(stats.norm.pdf(data, *params)))
                elif dist_name == 'lognormal':
                    log_likelihood = np.sum(np.log(stats.lognorm.pdf(data, *params)))
                elif dist_name == 'gamma':
                    log_likelihood = np.sum(np.log(stats.gamma.pdf(data, *params)))
                elif dist_name == 'beta':
                    log_likelihood = np.sum(np.log(stats.beta.pdf(scaled_data, *params)))
                elif dist_name == 'exponential':
                    log_likelihood = np.sum(np.log(stats.expon.pdf(data, *params)))
                else:
                    log_likelihood = 0
                
                aic = 2 * k - 2 * log_likelihood
                bic = k * np.log(n) - 2 * log_likelihood
                
                results[dist_name] = {
                    'parameters': params,
                    'ks_statistic': ks_stat,
                    'p_value': p_value,
                    'aic': aic,
                    'bic': bic,
                    'log_likelihood': log_likelihood
                }
                
            except Exception as e:
                logger.warning(f"Error fitting {dist_name} distribution: {e}")
                continue
        
        # Select best distribution based on AIC
        if results:
            best_dist = min(results.keys(), key=lambda x: results[x]['aic'])
            results['best_fit'] = {
                'distribution': best_dist,
                'parameters': results[best_dist]['parameters'],
                'aic': results[best_dist]['aic']
            }
        
        return results
    
    def bootstrap_analysis(self, data: pd.Series, n_bootstrap: int = 1000, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Bootstrap sampling and analysis"""
        logger.info(f"🔄 Running bootstrap analysis with {n_bootstrap} samples")
        
        try:
            bootstrap_samples = []
            
            for _ in range(n_bootstrap):
                sample = np.random.choice(data, size=len(data), replace=True)
                bootstrap_samples.append(np.mean(sample))
            
            bootstrap_samples = np.array(bootstrap_samples)
            
            # Calculate statistics
            mean_bootstrap = np.mean(bootstrap_samples)
            std_bootstrap = np.std(bootstrap_samples)
            
            # Confidence intervals
            alpha = 1 - confidence_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            ci_lower = np.percentile(bootstrap_samples, lower_percentile)
            ci_upper = np.percentile(bootstrap_samples, upper_percentile)
            
            # Bias calculation
            original_mean = np.mean(data)
            bias = mean_bootstrap - original_mean
            
            return {
                'bootstrap_mean': float(mean_bootstrap),
                'bootstrap_std': float(std_bootstrap),
                'confidence_interval': (float(ci_lower), float(ci_upper)),
                'bias': float(bias),
                'bias_corrected_mean': float(original_mean - bias),
                'n_bootstrap': n_bootstrap,
                'confidence_level': confidence_level
            }
            
        except Exception as e:
            logger.error(f"Error in bootstrap analysis: {e}")
            return {'error': str(e)}
    
    def bayesian_analysis(self, data: pd.Series, prior_mean: float = 0, prior_std: float = 1) -> Dict[str, Any]:
        """Bayesian inference for parameter estimation"""
        logger.info("🧠 Running Bayesian analysis")
        
        try:
            n = len(data)
            sample_mean = np.mean(data)
            sample_std = np.std(data, ddof=1)
            
            # Prior parameters
            mu_0 = prior_mean
            sigma_0 = prior_std
            
            # Posterior parameters (conjugate prior for normal distribution)
            precision_0 = 1 / (sigma_0 ** 2)
            precision_sample = n / (sample_std ** 2)
            precision_posterior = precision_0 + precision_sample
            
            mu_posterior = (precision_0 * mu_0 + precision_sample * sample_mean) / precision_posterior
            sigma_posterior = np.sqrt(1 / precision_posterior)
            
            # Credible intervals
            ci_lower = mu_posterior - 1.96 * sigma_posterior
            ci_upper = mu_posterior + 1.96 * sigma_posterior
            
            return {
                'posterior_mean': float(mu_posterior),
                'posterior_std': float(sigma_posterior),
                'credible_interval_95': (float(ci_lower), float(ci_upper)),
                'prior_mean': prior_mean,
                'prior_std': prior_std,
                'sample_size': n
            }
            
        except Exception as e:
            logger.error(f"Error in Bayesian analysis: {e}")
            return {'error': str(e)}

class RiskAnalyzer:
    """Risk analysis and portfolio optimization for fantasy lineups"""
    
    def __init__(self):
        self.risk_metrics = {}
        
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05) -> Dict[str, float]:
        """Calculate Value at Risk (VaR)"""
        try:
            # Historical simulation VaR
            var_historical = np.percentile(returns, confidence_level * 100)
            
            # Parametric VaR (assuming normal distribution)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            var_parametric = mean_return + norm.ppf(confidence_level) * std_return
            
            # Modified VaR (using Cornish-Fisher expansion)
            skewness = stats.skew(returns)
            kurtosis = stats.kurtosis(returns)
            
            z_cf = norm.ppf(confidence_level) + (skewness / 6) * (norm.ppf(confidence_level) ** 2 - 1) + \
                   (kurtosis / 24) * (norm.ppf(confidence_level) ** 3 - 3 * norm.ppf(confidence_level)) - \
                   (skewness ** 2 / 36) * (2 * norm.ppf(confidence_level) ** 3 - 5 * norm.ppf(confidence_level))
            
            var_modified = mean_return + z_cf * std_return
            
            return {
                'var_historical': float(var_historical),
                'var_parametric': float(var_parametric),
                'var_modified': float(var_modified),
                'confidence_level': confidence_level
            }
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return {'error': str(e)}
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.05) -> Dict[str, float]:
        """Calculate Conditional Value at Risk (CVaR) / Expected Shortfall"""
        try:
            var_threshold = np.percentile(returns, confidence_level * 100)
            tail_returns = returns[returns <= var_threshold]
            
            cvar = np.mean(tail_returns) if len(tail_returns) > 0 else var_threshold
            
            return {
                'cvar': float(cvar),
                'var_threshold': float(var_threshold),
                'tail_observations': len(tail_returns),
                'confidence_level': confidence_level
            }
            
        except Exception as e:
            logger.error(f"Error calculating CVaR: {e}")
            return {'error': str(e)}
    
    def portfolio_optimization(self, returns: pd.DataFrame, constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Modern portfolio theory optimization"""
        logger.info("📈 Running portfolio optimization")
        
        try:
            if constraints is None:
                constraints = {
                    'max_weight': 0.3,  # Maximum 30% in any single player
                    'min_weight': 0.0,  # No short selling
                    'target_return': None  # No target return constraint
                }
            
            # Calculate expected returns and covariance matrix
            expected_returns = returns.mean()
            cov_matrix = returns.cov()
            
            # Risk-free rate (assume 0 for fantasy)
            risk_free_rate = 0.0
            
            # Calculate Sharpe ratios
            excess_returns = expected_returns - risk_free_rate
            volatilities = np.sqrt(np.diag(cov_matrix))
            sharpe_ratios = excess_returns / volatilities
            
            # Simple optimization (equal weights for now)
            n_assets = len(expected_returns)
            equal_weights = np.ones(n_assets) / n_assets
            
            # Calculate portfolio metrics
            portfolio_return = np.dot(equal_weights, expected_returns)
            portfolio_variance = np.dot(equal_weights, np.dot(cov_matrix, equal_weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            portfolio_sharpe = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            return {
                'expected_returns': expected_returns.to_dict(),
                'covariance_matrix': cov_matrix.to_dict(),
                'sharpe_ratios': sharpe_ratios.to_dict(),
                'portfolio_return': float(portfolio_return),
                'portfolio_volatility': float(portfolio_volatility),
                'portfolio_sharpe': float(portfolio_sharpe),
                'weights': dict(zip(expected_returns.index, equal_weights))
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return {'error': str(e)}

class AdvancedAnalytics:
    """Main advanced analytics engine"""
    
    def __init__(self, database, models=None):
        self.db = database
        self.models = models or {}
        self.statistical_modeler = StatisticalModeler()
        self.risk_analyzer = RiskAnalyzer()
        
    def calculate_confidence_intervals(
        self, 
        predictions: np.ndarray, 
        confidence_level: float = 0.95,
        method: str = 'bootstrap'
    ) -> Dict[str, Any]:
        """Calculate confidence intervals for predictions"""
        logger.info(f"📊 Calculating {confidence_level*100}% confidence intervals using {method}")
        
        try:
            if method == 'bootstrap':
                # Bootstrap confidence intervals
                n_bootstrap = 1000
                bootstrap_samples = []
                
                for _ in range(n_bootstrap):
                    sample = np.random.choice(predictions, size=len(predictions), replace=True)
                    bootstrap_samples.append(np.mean(sample))
                
                bootstrap_samples = np.array(bootstrap_samples)
                alpha = 1 - confidence_level
                ci_lower = np.percentile(bootstrap_samples, (alpha / 2) * 100)
                ci_upper = np.percentile(bootstrap_samples, (1 - alpha / 2) * 100)
                
            elif method == 'parametric':
                # Parametric confidence intervals (assuming normal distribution)
                mean_pred = np.mean(predictions)
                std_pred = np.std(predictions)
                n = len(predictions)
                
                # Standard error
                se = std_pred / np.sqrt(n)
                
                # t-distribution critical value
                df = n - 1
                t_critical = t.ppf(1 - (1 - confidence_level) / 2, df)
                
                ci_lower = mean_pred - t_critical * se
                ci_upper = mean_pred + t_critical * se
                
            else:
                # Simple percentile method
                alpha = 1 - confidence_level
                ci_lower = np.percentile(predictions, (alpha / 2) * 100)
                ci_upper = np.percentile(predictions, (1 - alpha / 2) * 100)
            
            return {
                'confidence_level': confidence_level,
                'method': method,
                'mean': float(np.mean(predictions)),
                'std': float(np.std(predictions)),
                'confidence_interval': (float(ci_lower), float(ci_upper)),
                'margin_of_error': float((ci_upper - ci_lower) / 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return {'error': str(e)}
    
    def percentile_analysis(
        self, 
        player_data: pd.DataFrame, 
        percentiles: List[float] = None
    ) -> Dict[str, Any]:
        """Percentile-based ceiling/floor analysis"""
        logger.info("📈 Running percentile analysis")
        
        if percentiles is None:
            percentiles = [10, 25, 50, 75, 90, 95, 99]
        
        try:
            results = {}
            
            for player_id in player_data['player_id'].unique():
                player_games = player_data[player_data['player_id'] == player_id]
                
                if len(player_games) < 5:  # Need minimum games
                    continue
                
                fantasy_points = player_games['fantasy_points'].values
                
                # Calculate percentiles
                player_percentiles = {}
                for p in percentiles:
                    player_percentiles[f'p{p}'] = float(np.percentile(fantasy_points, p))
                
                # Additional metrics
                mean_fp = float(np.mean(fantasy_points))
                std_fp = float(np.std(fantasy_points))
                cv = std_fp / mean_fp if mean_fp > 0 else 0
                
                # Ceiling and floor analysis
                ceiling = player_percentiles['p90']
                floor = player_percentiles['p10']
                ceiling_floor_ratio = ceiling / floor if floor > 0 else 0
                
                # Consistency score (lower CV = more consistent)
                consistency_score = 1 / (1 + cv)
                
                results[player_id] = {
                    'mean_fp': mean_fp,
                    'std_fp': std_fp,
                    'cv': cv,
                    'consistency_score': consistency_score,
                    'ceiling': ceiling,
                    'floor': floor,
                    'ceiling_floor_ratio': ceiling_floor_ratio,
                    'percentiles': player_percentiles
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in percentile analysis: {e}")
            return {'error': str(e)}
    
    def correlation_analysis(
        self, 
        factors: pd.DataFrame, 
        method: str = 'pearson'
    ) -> Dict[str, Any]:
        """Factor correlation analysis"""
        logger.info(f"🔗 Running correlation analysis using {method} method")
        
        try:
            # Calculate correlation matrix
            correlation_matrix = factors.corr(method=method)
            
            # Find strong correlations
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # Strong correlation threshold
                        strong_correlations.append({
                            'factor1': correlation_matrix.columns[i],
                            'factor2': correlation_matrix.columns[j],
                            'correlation': float(corr_value)
                        })
            
            # Principal component analysis
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            
            scaler = StandardScaler()
            factors_scaled = scaler.fit_transform(factors.fillna(0))
            
            pca = PCA()
            pca.fit(factors_scaled)
            
            # Explained variance
            explained_variance_ratio = pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(explained_variance_ratio)
            
            # Components that explain 80% of variance
            n_components_80 = np.argmax(cumulative_variance >= 0.8) + 1
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'strong_correlations': strong_correlations,
                'explained_variance_ratio': explained_variance_ratio.tolist(),
                'cumulative_variance': cumulative_variance.tolist(),
                'n_components_80_percent': int(n_components_80),
                'method': method
            }
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return {'error': str(e)}
    
    def time_series_analysis(
        self, 
        player_data: pd.DataFrame, 
        periods: int = 30
    ) -> Dict[str, Any]:
        """Time series analysis for trends"""
        logger.info(f"📈 Running time series analysis for {periods} periods")
        
        try:
            results = {}
            
            for player_id in player_data['player_id'].unique():
                player_games = player_data[player_data['player_id'] == player_id].tail(periods)
                
                if len(player_games) < 10:  # Need minimum data
                    continue
                
                # Sort by date
                player_games = player_games.sort_values('game_date')
                fantasy_points = player_games['fantasy_points'].values
                
                # Trend analysis
                x = np.arange(len(fantasy_points))
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, fantasy_points)
                
                # Moving averages
                ma_5 = pd.Series(fantasy_points).rolling(window=5, min_periods=1).mean()
                ma_10 = pd.Series(fantasy_points).rolling(window=10, min_periods=1).mean()
                
                # Momentum indicators
                momentum_5 = ma_5.iloc[-1] - ma_5.iloc[-6] if len(ma_5) >= 6 else 0
                momentum_10 = ma_10.iloc[-1] - ma_10.iloc[-11] if len(ma_10) >= 11 else 0
                
                # Seasonality analysis (day of week, month effects)
                if 'game_date' in player_games.columns:
                    player_games['game_date'] = pd.to_datetime(player_games['game_date'])
                    player_games['day_of_week'] = player_games['game_date'].dt.dayofweek
                    player_games['month'] = player_games['game_date'].dt.month
                    
                    # Day of week effect
                    dow_means = player_games.groupby('day_of_week')['fantasy_points'].mean()
                    best_dow = dow_means.idxmax()
                    worst_dow = dow_means.idxmin()
                    
                    # Monthly effect
                    monthly_means = player_games.groupby('month')['fantasy_points'].mean()
                    best_month = monthly_means.idxmax()
                    worst_month = monthly_means.idxmin()
                else:
                    best_dow = worst_dow = best_month = worst_month = None
                
                results[player_id] = {
                    'trend_slope': float(slope),
                    'trend_r_squared': float(r_value ** 2),
                    'trend_p_value': float(p_value),
                    'momentum_5_game': float(momentum_5),
                    'momentum_10_game': float(momentum_10),
                    'best_day_of_week': int(best_dow) if best_dow is not None else None,
                    'worst_day_of_week': int(worst_dow) if worst_dow is not None else None,
                    'best_month': int(best_month) if best_month is not None else None,
                    'worst_month': int(worst_month) if worst_month is not None else None,
                    'recent_5_game_avg': float(ma_5.iloc[-1]) if len(ma_5) > 0 else 0,
                    'recent_10_game_avg': float(ma_10.iloc[-1]) if len(ma_10) > 0 else 0
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in time series analysis: {e}")
            return {'error': str(e)}
    
    def monte_carlo_risk_analysis(
        self, 
        lineup_data: List[Dict[str, Any]], 
        iterations: int = 10000
    ) -> Dict[str, Any]:
        """Monte Carlo risk analysis for lineups"""
        logger.info(f"🎲 Running Monte Carlo risk analysis with {iterations} iterations")
        
        try:
            # Extract player projections
            player_projections = []
            for player in lineup_data:
                player_projections.append({
                    'player_id': player['player_id'],
                    'mean': player.get('mean_projection', 0),
                    'std': player.get('std_projection', 1),
                    'salary': player.get('salary', 0)
                })
            
            # Run Monte Carlo simulation
            simulation_results = []
            
            for _ in range(iterations):
                iteration_score = 0
                iteration_salary = 0
                
                for player in player_projections:
                    # Sample from normal distribution
                    sample = np.random.normal(player['mean'], player['std'])
                    iteration_score += max(0, sample)  # Ensure non-negative
                    iteration_salary += player['salary']
                
                simulation_results.append({
                    'total_score': iteration_score,
                    'total_salary': iteration_salary,
                    'value_score': iteration_score / (iteration_salary / 1000) if iteration_salary > 0 else 0
                })
            
            simulation_df = pd.DataFrame(simulation_results)
            
            # Calculate risk metrics
            returns = simulation_df['total_score']
            
            # VaR and CVaR
            var_95 = self.risk_analyzer.calculate_var(returns, 0.05)
            cvar_95 = self.risk_analyzer.calculate_cvar(returns, 0.05)
            
            # Portfolio optimization
            portfolio_metrics = self.risk_analyzer.portfolio_optimization(
                pd.DataFrame({f'player_{i}': [p['mean'] for p in player_projections] for i in range(len(player_projections))})
            )
            
            # Additional risk metrics
            mean_score = np.mean(returns)
            std_score = np.std(returns)
            sharpe_ratio = mean_score / std_score if std_score > 0 else 0
            
            # Downside risk
            downside_returns = returns[returns < mean_score]
            downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 0
            
            # Maximum drawdown simulation
            cumulative_scores = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_scores)
            drawdowns = cumulative_scores - running_max
            max_drawdown = np.min(drawdowns)
            
            return {
                'mean_score': float(mean_score),
                'std_score': float(std_score),
                'sharpe_ratio': float(sharpe_ratio),
                'var_95': var_95,
                'cvar_95': cvar_95,
                'downside_deviation': float(downside_deviation),
                'max_drawdown': float(max_drawdown),
                'portfolio_metrics': portfolio_metrics,
                'percentiles': {
                    'p10': float(np.percentile(returns, 10)),
                    'p25': float(np.percentile(returns, 25)),
                    'p50': float(np.percentile(returns, 50)),
                    'p75': float(np.percentile(returns, 75)),
                    'p90': float(np.percentile(returns, 90))
                },
                'iterations': iterations
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo risk analysis: {e}")
            return {'error': str(e)}

def main():
    """Test the advanced analytics engine"""
    logger.info("🧪 Testing Advanced Analytics Engine...")
    
    # Create mock database
    class MockDatabase:
        def get_dataframe(self, query, params=None):
            return pd.DataFrame({
                'player_id': [1, 2, 3, 1, 2, 3],
                'fantasy_points': [25.5, 18.2, 32.1, 28.3, 15.8, 29.7],
                'game_date': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-16', '2024-01-16', '2024-01-16']
            })
    
    # Initialize analytics engine
    analytics = AdvancedAnalytics(MockDatabase())
    
    # Test statistical modeling
    test_data = pd.Series([25, 30, 20, 28, 22, 35, 18, 32, 26, 29])
    distributions = analytics.statistical_modeler.fit_distributions(test_data)
    logger.info(f"Distribution fitting test: {len(distributions)} distributions fitted")
    
    # Test bootstrap analysis
    bootstrap_results = analytics.statistical_modeler.bootstrap_analysis(test_data, n_bootstrap=100)
    logger.info(f"Bootstrap analysis test: {bootstrap_results.get('bootstrap_mean', 'Error')}")

if __name__ == "__main__":
    main()

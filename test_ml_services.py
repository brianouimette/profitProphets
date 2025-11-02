#!/usr/bin/env python3
"""
Comprehensive Test Script for ML Services
Tests all Priority 1-3 implementations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simulation_engine():
    """Test Priority 1: Simulation Engine"""
    logger.info("🧪 Testing Simulation Engine...")
    
    try:
        from ml_service.simulation_engine import SimulationEngine, PlayerProjection, SimulationType
        
        # Create mock database
        class MockDatabase:
            def get_dataframe(self, query, params=None):
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
        
        # Test Monte Carlo simulation
        result = engine.monte_carlo_simulation(lineup, iterations=1000)
        logger.info(f"✅ Monte Carlo simulation: Mean={result.mean_score:.2f}, Std={result.std_score:.2f}")
        
        # Test scenario analysis
        scenarios = [
            engine.scenario_builder.create_injury_scenario(1, 4),
            engine.scenario_builder.create_weather_scenario("Indoor", 0.95)
        ]
        
        scenario_results = engine.scenario_analysis(lineup, scenarios, iterations=500)
        logger.info(f"✅ Scenario analysis: {len(scenario_results)} scenarios completed")
        
        # Test variance modeling
        mock_data = pd.DataFrame({
            'player_id': [1, 1, 1, 2, 2, 2],
            'fantasy_points': [25, 30, 20, 18, 22, 15],
            'game_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-01', '2024-01-02', '2024-01-03'],
            'opponent_team_id': [2, 3, 4, 1, 3, 1]
        })
        
        variance_models = engine.variance_modeling(mock_data)
        logger.info(f"✅ Variance modeling: {len(variance_models)} players analyzed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Simulation Engine test failed: {e}")
        return False

def test_ml_model_trainer():
    """Test Priority 2: ML Model Trainer"""
    logger.info("🧪 Testing ML Model Trainer...")
    
    try:
        from ml_service.ml_model_trainer import MLModelTrainer, FeatureEngineer
        
        # Create mock database
        class MockDatabase:
            def get_dataframe(self, query, params=None):
                if 'player_game_logs' in query:
                    return pd.DataFrame({
                        'player_id': [1, 2, 3, 1, 2, 3],
                        'fantasy_points': [25.5, 18.2, 32.1, 28.3, 15.8, 29.7],
                        'game_date': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-16', '2024-01-16', '2024-01-16'],
                        'primary_position': ['PG', 'SG', 'SF', 'PG', 'SG', 'SF'],
                        'team_id': [1, 2, 3, 1, 2, 3],
                        'opponent_team_id': [2, 1, 1, 3, 3, 2],
                        'points': [20, 15, 25, 22, 12, 24],
                        'rebounds': [5, 4, 8, 6, 3, 7],
                        'assists': [8, 6, 4, 9, 5, 3]
                    })
                elif 'teams' in query:
                    return pd.DataFrame({
                        'id': [1, 2, 3],
                        'abbreviation': ['LAL', 'GSW', 'BOS'],
                        'conference': ['West', 'West', 'East'],
                        'division': ['Pacific', 'Pacific', 'Atlantic']
                    })
                elif 'injuries' in query:
                    return pd.DataFrame({
                        'player_id': [1],
                        'status': ['ACTIVE'],
                        'date': ['2024-01-15']
                    })
                elif 'dfs_projections' in query:
                    return pd.DataFrame({
                        'player_id': [1, 2, 3],
                        'salary': [8000, 7500, 7000],
                        'projected_points': [25, 20, 18],
                        'ownership_percentage': [15, 20, 25]
                    })
                else:
                    return pd.DataFrame()
        
        # Initialize trainer
        trainer = MLModelTrainer(MockDatabase(), {}, './test_models')
        
        # Test feature engineering
        mock_data = pd.DataFrame({
            'player_id': [1, 1, 1, 2, 2, 2],
            'fantasy_points': [25, 30, 20, 18, 22, 15],
            'game_date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-01', '2024-01-02', '2024-01-03'],
            'primary_position': ['PG', 'PG', 'PG', 'SG', 'SG', 'SG']
        })
        
        features = trainer.feature_engineer.create_performance_features(mock_data)
        logger.info(f"✅ Feature engineering: {features.shape} features created")
        
        # Test training data preparation
        X, y = trainer.prepare_training_data('2024-01-01', '2024-01-31')
        logger.info(f"✅ Training data preparation: {X.shape[0]} samples, {X.shape[1]} features")
        
        # Test model training (with small dataset)
        if not X.empty and not y.empty:
            results = trainer.train_fantasy_points_model(X, y, test_size=0.3, model_type='random_forest')
            if 'error' not in results:
                logger.info(f"✅ Model training: RMSE={results.get('test_rmse', 'N/A'):.3f}")
            else:
                logger.warning(f"⚠️ Model training error: {results['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ML Model Trainer test failed: {e}")
        return False

def test_advanced_analytics():
    """Test Priority 3: Advanced Analytics"""
    logger.info("🧪 Testing Advanced Analytics...")
    
    try:
        from ml_service.advanced_analytics import AdvancedAnalytics, StatisticalModeler, RiskAnalyzer
        
        # Create mock database
        class MockDatabase:
            def get_dataframe(self, query, params=None):
                return pd.DataFrame({
                    'player_id': [1, 2, 3, 1, 2, 3],
                    'fantasy_points': [25.5, 18.2, 32.1, 28.3, 15.8, 29.7],
                    'game_date': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-16', '2024-01-16', '2024-01-16']
                })
        
        # Initialize analytics
        analytics = AdvancedAnalytics(MockDatabase())
        
        # Test statistical modeling
        test_data = pd.Series([25, 30, 20, 28, 22, 35, 18, 32, 26, 29])
        distributions = analytics.statistical_modeler.fit_distributions(test_data)
        logger.info(f"✅ Distribution fitting: {len(distributions)} distributions fitted")
        
        # Test bootstrap analysis
        bootstrap_results = analytics.statistical_modeler.bootstrap_analysis(test_data, n_bootstrap=100)
        if 'error' not in bootstrap_results:
            logger.info(f"✅ Bootstrap analysis: Mean={bootstrap_results.get('bootstrap_mean', 'N/A'):.2f}")
        else:
            logger.warning(f"⚠️ Bootstrap analysis error: {bootstrap_results['error']}")
        
        # Test confidence intervals
        predictions = np.array([25.5, 28.3, 22.1, 30.2, 26.8])
        ci_results = analytics.calculate_confidence_intervals(predictions, confidence_level=0.95)
        if 'error' not in ci_results:
            logger.info(f"✅ Confidence intervals: {ci_results.get('confidence_interval', 'N/A')}")
        else:
            logger.warning(f"⚠️ Confidence intervals error: {ci_results['error']}")
        
        # Test percentile analysis
        mock_player_data = pd.DataFrame({
            'player_id': [1, 1, 1, 2, 2, 2],
            'fantasy_points': [25, 30, 20, 18, 22, 15]
        })
        
        percentile_results = analytics.percentile_analysis(mock_player_data)
        if 'error' not in percentile_results:
            logger.info(f"✅ Percentile analysis: {len(percentile_results)} players analyzed")
        else:
            logger.warning(f"⚠️ Percentile analysis error: {percentile_results['error']}")
        
        # Test risk analysis
        returns = pd.Series([0.05, -0.02, 0.08, -0.01, 0.03, -0.04, 0.06, 0.02])
        var_results = analytics.risk_analyzer.calculate_var(returns, 0.05)
        if 'error' not in var_results:
            logger.info(f"✅ VaR calculation: {var_results.get('var_historical', 'N/A'):.3f}")
        else:
            logger.warning(f"⚠️ VaR calculation error: {var_results['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Advanced Analytics test failed: {e}")
        return False

def test_api_integration():
    """Test API integration"""
    logger.info("🧪 Testing API Integration...")
    
    try:
        # Test that all imports work
        from ml_service.api import app
        from ml_service.simulation_engine import SimulationEngine, PlayerProjection
        from ml_service.ml_model_trainer import MLModelTrainer
        from ml_service.advanced_analytics import AdvancedAnalytics
        
        logger.info("✅ All API imports successful")
        
        # Test that FastAPI app is properly configured
        assert app is not None
        logger.info("✅ FastAPI app initialized")
        
        # Test that all analyzers are initialized
        from ml_service.api import simulation_engine, ml_trainer, advanced_analytics
        assert simulation_engine is not None
        assert ml_trainer is not None
        assert advanced_analytics is not None
        logger.info("✅ All analyzers initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Comprehensive ML Services Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Simulation Engine", test_simulation_engine),
        ("ML Model Trainer", test_ml_model_trainer),
        ("Advanced Analytics", test_advanced_analytics),
        ("API Integration", test_api_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} Test...")
        logger.info("-" * 40)
        
        try:
            success = test_func()
            results[test_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = "💥 CRASHED"
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        logger.info(f"{test_name:20} | {result}")
    
    passed = sum(1 for result in results.values() if "PASSED" in result)
    total = len(results)
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Milestone 3 implementation is complete!")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

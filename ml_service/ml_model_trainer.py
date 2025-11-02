"""
ML Model Training System
Advanced machine learning models for NBA fantasy prediction
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
import joblib
import os
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import Ridge, Lasso
from sklearn.neural_network import MLPRegressor
# XGBoost and LightGBM will be imported conditionally to avoid dependency issues
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Advanced feature engineering for ML models"""
    
    def __init__(self, database):
        self.db = database
        self.scalers = {}
        self.encoders = {}
        
    def create_performance_features(self, player_data: pd.DataFrame, games_back: int = 15) -> pd.DataFrame:
        """Create recent performance features"""
        logger.info(f"🔧 Creating performance features for {games_back} games back")
        
        features = player_data.copy()
        
        # Sort by player and date
        features = features.sort_values(['player_id', 'game_date'])
        
        # Recent performance metrics
        for window in [3, 5, 10, 15]:
            if window <= games_back:
                features[f'avg_fantasy_points_{window}g'] = features.groupby('player_id')['fantasy_points'].rolling(window=window, min_periods=1).mean().values
                features[f'std_fantasy_points_{window}g'] = features.groupby('player_id')['fantasy_points'].rolling(window=window, min_periods=1).std().values
                features[f'max_fantasy_points_{window}g'] = features.groupby('player_id')['fantasy_points'].rolling(window=window, min_periods=1).max().values
                features[f'min_fantasy_points_{window}g'] = features.groupby('player_id')['fantasy_points'].rolling(window=window, min_periods=1).min().values
        
        # Trend analysis
        features['fantasy_points_trend_5g'] = features.groupby('player_id')['fantasy_points'].rolling(window=5, min_periods=3).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 3 else 0
        ).values
        
        # Consistency metrics
        features['consistency_score'] = 1 - (features['std_fantasy_points_10g'] / (features['avg_fantasy_points_10g'] + 1e-8))
        features['volatility_score'] = features['std_fantasy_points_10g'] / (features['avg_fantasy_points_10g'] + 1e-8)
        
        # Performance momentum
        features['momentum_3g'] = features['avg_fantasy_points_3g'] - features['avg_fantasy_points_10g']
        features['momentum_5g'] = features['avg_fantasy_points_5g'] - features['avg_fantasy_points_15g']
        
        return features
    
    def create_matchup_features(self, player_data: pd.DataFrame, team_data: pd.DataFrame) -> pd.DataFrame:
        """Create matchup-specific features"""
        logger.info("🔧 Creating matchup features")
        
        features = player_data.copy()
        
        # Merge with team data
        if 'opponent_team_id' in features.columns:
            team_features = team_data[['id', 'abbreviation', 'conference', 'division']].rename(
                columns={'id': 'opponent_team_id', 'abbreviation': 'opponent_abbreviation'}
            )
            features = features.merge(team_features, on='opponent_team_id', how='left')
        
        # Historical matchup performance
        for player_id in features['player_id'].unique():
            player_mask = features['player_id'] == player_id
            player_games = features[player_mask].copy()
            
            if len(player_games) < 5:
                continue
            
            # Calculate opponent-specific averages
            if 'opponent_team_id' in player_games.columns:
                for opponent in player_games['opponent_team_id'].unique():
                    if pd.notna(opponent):
                        opponent_games = player_games[player_games['opponent_team_id'] == opponent]
                        if len(opponent_games) > 1:
                            avg_vs_opponent = opponent_games['fantasy_points'].mean()
                            features.loc[player_mask & (features['opponent_team_id'] == opponent), 'avg_vs_opponent'] = avg_vs_opponent
        
        # Position vs opponent analysis
        if 'primary_position' in features.columns and 'opponent_team_id' in features.columns:
            for position in features['primary_position'].unique():
                if pd.notna(position):
                    pos_games = features[features['primary_position'] == position]
                    for opponent in pos_games['opponent_team_id'].unique():
                        if pd.notna(opponent):
                            opponent_pos_games = pos_games[pos_games['opponent_team_id'] == opponent]
                            if len(opponent_pos_games) > 1:
                                avg_pos_vs_opponent = opponent_pos_games['fantasy_points'].mean()
                                mask = (features['primary_position'] == position) & (features['opponent_team_id'] == opponent)
                                features.loc[mask, 'avg_position_vs_opponent'] = avg_pos_vs_opponent
        
        return features
    
    def create_contextual_features(self, game_data: pd.DataFrame) -> pd.DataFrame:
        """Create contextual features (rest days, home/away, etc.)"""
        logger.info("🔧 Creating contextual features")
        
        features = game_data.copy()
        
        # Rest days calculation
        if 'game_date' in features.columns and 'player_id' in features.columns:
            features['game_date'] = pd.to_datetime(features['game_date'])
            features = features.sort_values(['player_id', 'game_date'])
            
            features['rest_days'] = features.groupby('player_id')['game_date'].diff().dt.days.fillna(0)
            features['is_back_to_back'] = (features['rest_days'] == 1).astype(int)
            features['is_3_in_4'] = features.groupby('player_id')['rest_days'].rolling(window=3, min_periods=3).apply(
                lambda x: (x == 1).sum() >= 2 if len(x) >= 3 else 0
            ).values.astype(int)
        
        # Home/away features
        if 'home_team_id' in features.columns and 'team_id' in features.columns:
            features['is_home'] = (features['team_id'] == features['home_team_id']).astype(int)
        
        # Season context
        if 'game_date' in features.columns:
            features['month'] = pd.to_datetime(features['game_date']).dt.month
            features['day_of_week'] = pd.to_datetime(features['game_date']).dt.dayofweek
            features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        # Game importance (playoff race, etc.)
        features['game_importance'] = 1.0  # Placeholder - would need more context
        
        return features
    
    def create_team_features(self, team_data: pd.DataFrame, game_data: pd.DataFrame) -> pd.DataFrame:
        """Create team-level features"""
        logger.info("🔧 Creating team features")
        
        features = game_data.copy()
        
        # Team performance trends
        if 'team_id' in features.columns and 'game_date' in features.columns:
            features['game_date'] = pd.to_datetime(features['game_date'])
            features = features.sort_values(['team_id', 'game_date'])
            
            # Team's recent performance
            for window in [5, 10, 15]:
                features[f'team_avg_points_{window}g'] = features.groupby('team_id')['points'].rolling(window=window, min_periods=1).mean().values
                features[f'team_avg_rebounds_{window}g'] = features.groupby('team_id')['rebounds'].rolling(window=window, min_periods=1).mean().values
                features[f'team_avg_assists_{window}g'] = features.groupby('team_id')['assists'].rolling(window=window, min_periods=1).mean().values
        
        # Team vs team historical performance
        if 'opponent_team_id' in features.columns and 'team_id' in features.columns:
            for team_id in features['team_id'].unique():
                team_games = features[features['team_id'] == team_id]
                for opponent in team_games['opponent_team_id'].unique():
                    if pd.notna(opponent):
                        opponent_games = team_games[team_games['opponent_team_id'] == opponent]
                        if len(opponent_games) > 1:
                            avg_vs_opponent = opponent_games['fantasy_points'].mean()
                            mask = (features['team_id'] == team_id) & (features['opponent_team_id'] == opponent)
                            features.loc[mask, 'team_avg_vs_opponent'] = avg_vs_opponent
        
        return features
    
    def create_injury_features(self, injury_data: pd.DataFrame, player_data: pd.DataFrame) -> pd.DataFrame:
        """Create injury-related features"""
        logger.info("🔧 Creating injury features")
        
        features = player_data.copy()
        
        if injury_data.empty:
            features['is_injured'] = 0
            features['injury_risk_score'] = 0
            return features
        
        # Current injury status
        active_injuries = injury_data[injury_data['status'] == 'ACTIVE']
        features['is_injured'] = features['player_id'].isin(active_injuries['player_id']).astype(int)
        
        # Injury history
        features['total_injuries'] = features['player_id'].map(
            injury_data.groupby('player_id').size()
        ).fillna(0)
        
        # Recent injury frequency
        if 'game_date' in features.columns:
            features['game_date'] = pd.to_datetime(features['game_date'])
            recent_cutoff = features['game_date'].max() - timedelta(days=30)
            recent_injuries = injury_data[pd.to_datetime(injury_data['date']) >= recent_cutoff]
            features['recent_injuries'] = features['player_id'].map(
                recent_injuries.groupby('player_id').size()
            ).fillna(0)
        
        # Injury risk score (simplified)
        features['injury_risk_score'] = (
            features['total_injuries'] * 0.3 + 
            features['recent_injuries'] * 0.7
        )
        
        return features
    
    def create_salary_features(self, salary_data: pd.DataFrame, player_data: pd.DataFrame) -> pd.DataFrame:
        """Create salary-based features"""
        logger.info("🔧 Creating salary features")
        
        features = player_data.copy()
        
        if salary_data.empty:
            features['salary'] = 0
            features['salary_tier'] = 'Unknown'
            features['value_score'] = 0
            return features
        
        # Merge salary data
        salary_features = salary_data[['player_id', 'salary', 'projected_points', 'ownership_percentage']].copy()
        features = features.merge(salary_features, on='player_id', how='left')
        
        # Salary tiers
        if 'salary' in features.columns:
            features['salary_tier'] = pd.cut(
                features['salary'], 
                bins=[0, 5000, 7000, 9000, 11000, float('inf')],
                labels=['Minimum', 'Low', 'Mid', 'High', 'Elite']
            )
        
        # Value metrics
        if 'salary' in features.columns and 'projected_points' in features.columns:
            features['value_score'] = features['projected_points'] / (features['salary'] / 1000)
            features['points_per_dollar'] = features['projected_points'] / features['salary']
        
        # Ownership analysis
        if 'ownership_percentage' in features.columns:
            features['ownership_tier'] = pd.cut(
                features['ownership_percentage'],
                bins=[0, 5, 15, 25, 50, 100],
                labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
            )
        
        return features

class MLModelTrainer:
    """Advanced ML model training system"""
    
    def __init__(self, database, config, model_cache_dir='./ml_models'):
        self.db = database
        self.config = config
        self.model_cache_dir = model_cache_dir
        self.feature_engineer = FeatureEngineer(database)
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Create model cache directory
        os.makedirs(self.model_cache_dir, exist_ok=True)
    
    def prepare_training_data(
        self, 
        start_date: str, 
        end_date: str,
        min_games_per_player: int = 10
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare comprehensive training dataset"""
        logger.info(f"📊 Preparing training data from {start_date} to {end_date}")
        
        try:
            # Get base player game logs
            query = """
            SELECT 
                pgl.*,
                p.first_name,
                p.last_name,
                p.primary_position,
                t.abbreviation as team_abbreviation,
                g.game_date,
                g.home_team_id,
                g.away_team_id,
                g.status
            FROM player_game_logs pgl
            JOIN players p ON pgl.player_id = p.id
            JOIN teams t ON pgl.team_id = t.id
            JOIN games g ON pgl.game_id = g.id
            WHERE g.game_date BETWEEN %s AND %s
            AND g.status = 'FINAL'
            ORDER BY g.game_date, pgl.player_id
            """
            
            base_data = self.db.get_dataframe(query, params=[start_date, end_date])
            
            if base_data.empty:
                logger.warning("No training data found")
                return pd.DataFrame(), pd.Series()
            
            # Filter players with minimum games
            player_game_counts = base_data['player_id'].value_counts()
            valid_players = player_game_counts[player_game_counts >= min_games_per_player].index
            base_data = base_data[base_data['player_id'].isin(valid_players)]
            
            logger.info(f"Training data: {len(base_data)} records for {len(valid_players)} players")
            
            # Create features
            features_data = self.feature_engineer.create_performance_features(base_data)
            features_data = self.feature_engineer.create_contextual_features(features_data)
            
            # Add team features
            team_data = self.db.get_dataframe("SELECT * FROM teams")
            features_data = self.feature_engineer.create_team_features(team_data, features_data)
            
            # Add injury features
            injury_data = self.db.get_dataframe("SELECT * FROM injuries")
            features_data = self.feature_engineer.create_injury_features(injury_data, features_data)
            
            # Add salary features
            salary_data = self.db.get_dataframe("SELECT * FROM dfs_projections")
            features_data = self.feature_engineer.create_salary_features(salary_data, features_data)
            
            # Prepare target variable
            target = features_data['fantasy_points']
            
            # Remove non-feature columns
            feature_columns = [col for col in features_data.columns 
                             if col not in ['player_id', 'game_id', 'game_date', 'fantasy_points', 'first_name', 'last_name']]
            
            X = features_data[feature_columns]
            y = target
            
            # Handle missing values
            X = X.fillna(X.median())
            
            # Encode categorical variables
            categorical_columns = X.select_dtypes(include=['object']).columns
            for col in categorical_columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    X[col] = self.encoders[col].fit_transform(X[col].astype(str))
                else:
                    X[col] = self.encoders[col].transform(X[col].astype(str))
            
            logger.info(f"✅ Training data prepared: {X.shape[0]} samples, {X.shape[1]} features")
            return X, y
            
        except Exception as e:
            logger.error(f"❌ Error preparing training data: {e}")
            return pd.DataFrame(), pd.Series()
    
    def train_fantasy_points_model(
        self, 
        X: pd.DataFrame, 
        y: pd.Series,
        test_size: float = 0.2,
        model_type: str = 'random_forest'
    ) -> Dict[str, Any]:
        """Train RandomForestRegressor for fantasy points prediction"""
        logger.info(f"🤖 Training {model_type} model for fantasy points prediction")
        
        try:
            # Time series split for validation
            tscv = TimeSeriesSplit(n_splits=5)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers['fantasy_points'] = scaler
            
            # Initialize model
            if model_type == 'random_forest':
                model = RandomForestRegressor(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            elif model_type == 'gradient_boosting':
                model = GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=8,
                    random_state=42
                )
            elif model_type == 'xgboost':
                try:
                    import xgboost as xgb
                    model = xgb.XGBRegressor(
                        n_estimators=200,
                        learning_rate=0.1,
                        max_depth=8,
                        random_state=42,
                        n_jobs=-1
                    )
                except ImportError:
                    logger.warning("XGBoost not available, falling back to RandomForest")
                    model = RandomForestRegressor(n_estimators=200, random_state=42)
            elif model_type == 'lightgbm':
                try:
                    import lightgbm as lgb
                    model = lgb.LGBMRegressor(
                        n_estimators=200,
                        learning_rate=0.1,
                        max_depth=8,
                        random_state=42,
                        n_jobs=-1,
                        verbose=-1
                    )
                except ImportError:
                    logger.warning("LightGBM not available, falling back to RandomForest")
                    model = RandomForestRegressor(n_estimators=200, random_state=42)
            elif model_type == 'neural_network':
                model = MLPRegressor(
                    hidden_layer_sizes=(100, 50, 25),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    learning_rate='adaptive',
                    max_iter=500,
                    random_state=42
                )
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred_train = model.predict(X_train_scaled)
            y_pred_test = model.predict(X_test_scaled)
            
            # Calculate metrics
            train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            train_mae = mean_absolute_error(y_train, y_pred_train)
            test_mae = mean_absolute_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=tscv, scoring='neg_mean_squared_error')
            cv_rmse = np.sqrt(-cv_scores.mean())
            cv_std = np.sqrt(cv_scores.std())
            
            # Feature importance
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = pd.DataFrame({
                    'feature': X.columns,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
            
            # Store model
            self.models['fantasy_points'] = model
            
            # Save model
            model_path = os.path.join(self.model_cache_dir, f'fantasy_points_{model_type}.joblib')
            joblib.dump({
                'model': model,
                'scaler': scaler,
                'encoders': self.encoders,
                'feature_columns': X.columns.tolist()
            }, model_path)
            
            results = {
                'model_type': model_type,
                'train_rmse': float(train_rmse),
                'test_rmse': float(test_rmse),
                'train_mae': float(train_mae),
                'test_mae': float(test_mae),
                'train_r2': float(train_r2),
                'test_r2': float(test_r2),
                'cv_rmse': float(cv_rmse),
                'cv_std': float(cv_std),
                'feature_importance': feature_importance.to_dict() if feature_importance is not None else None,
                'model_path': model_path
            }
            
            logger.info(f"✅ Model training completed: Test RMSE={test_rmse:.3f}, Test R²={test_r2:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error training fantasy points model: {e}")
            return {'error': str(e)}
    
    def train_value_model(
        self, 
        salary_data: pd.DataFrame, 
        projections: pd.DataFrame
    ) -> Dict[str, Any]:
        """Train model for value identification"""
        logger.info("🤖 Training value identification model")
        
        try:
            # Merge salary and projection data
            value_data = salary_data.merge(projections, on='player_id', how='inner')
            
            # Create value features
            value_data['salary_tier'] = pd.cut(
                value_data['salary'], 
                bins=[0, 5000, 7000, 9000, 11000, float('inf')],
                labels=[0, 1, 2, 3, 4]
            )
            
            value_data['value_score'] = value_data['projected_points'] / (value_data['salary'] / 1000)
            value_data['points_per_dollar'] = value_data['projected_points'] / value_data['salary']
            
            # Prepare features
            feature_columns = ['salary', 'salary_tier', 'ownership_percentage', 'projected_points']
            X = value_data[feature_columns].fillna(0)
            y = value_data['value_score']
            
            # Train model
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            test_r2 = r2_score(y_test, y_pred)
            
            # Store model
            self.models['value'] = model
            
            # Save model
            model_path = os.path.join(self.model_cache_dir, 'value_model.joblib')
            joblib.dump({
                'model': model,
                'feature_columns': feature_columns
            }, model_path)
            
            results = {
                'model_type': 'gradient_boosting',
                'test_rmse': float(test_rmse),
                'test_r2': float(test_r2),
                'model_path': model_path
            }
            
            logger.info(f"✅ Value model training completed: Test RMSE={test_rmse:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error training value model: {e}")
            return {'error': str(e)}
    
    def train_injury_risk_model(
        self, 
        injury_data: pd.DataFrame, 
        performance_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Train model for injury risk assessment"""
        logger.info("🤖 Training injury risk model")
        
        try:
            # Create injury features
            injury_features = self.feature_engineer.create_injury_features(injury_data, performance_data)
            
            # Prepare features
            feature_columns = ['total_injuries', 'recent_injuries', 'injury_risk_score']
            X = injury_features[feature_columns].fillna(0)
            
            # Create target (binary: injured or not)
            y = (injury_features['is_injured'] > 0).astype(int)
            
            if y.sum() < 10:  # Need minimum positive cases
                logger.warning("Insufficient injury data for training")
                return {'error': 'Insufficient injury data'}
            
            # Train model
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            from sklearn.metrics import accuracy_score, classification_report
            accuracy = accuracy_score(y_test, y_pred)
            
            # Store model
            self.models['injury_risk'] = model
            
            # Save model
            model_path = os.path.join(self.model_cache_dir, 'injury_risk_model.joblib')
            joblib.dump({
                'model': model,
                'feature_columns': feature_columns
            }, model_path)
            
            results = {
                'model_type': 'random_forest_classifier',
                'accuracy': float(accuracy),
                'model_path': model_path
            }
            
            logger.info(f"✅ Injury risk model training completed: Accuracy={accuracy:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error training injury risk model: {e}")
            return {'error': str(e)}
    
    def save_models(self) -> Dict[str, str]:
        """Persist all trained models with metadata"""
        logger.info("💾 Saving all trained models")
        
        saved_models = {}
        
        for model_name, model in self.models.items():
            try:
                model_path = os.path.join(self.model_cache_dir, f'{model_name}_model.joblib')
                
                model_data = {
                    'model': model,
                    'scaler': self.scalers.get(model_name),
                    'encoders': self.encoders,
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0'
                }
                
                joblib.dump(model_data, model_path)
                saved_models[model_name] = model_path
                
            except Exception as e:
                logger.error(f"Error saving {model_name} model: {e}")
        
        logger.info(f"✅ Saved {len(saved_models)} models")
        return saved_models
    
    def load_models(self) -> Dict[str, bool]:
        """Load pre-trained models"""
        logger.info("📂 Loading pre-trained models")
        
        loaded_models = {}
        
        for model_name in ['fantasy_points', 'value', 'injury_risk']:
            try:
                model_path = os.path.join(self.model_cache_dir, f'{model_name}_model.joblib')
                
                if os.path.exists(model_path):
                    model_data = joblib.load(model_path)
                    self.models[model_name] = model_data['model']
                    
                    if 'scaler' in model_data:
                        self.scalers[model_name] = model_data['scaler']
                    if 'encoders' in model_data:
                        self.encoders.update(model_data['encoders'])
                    
                    loaded_models[model_name] = True
                    logger.info(f"✅ Loaded {model_name} model")
                else:
                    loaded_models[model_name] = False
                    logger.warning(f"⚠️ Model {model_name} not found")
                    
            except Exception as e:
                logger.error(f"Error loading {model_name} model: {e}")
                loaded_models[model_name] = False
        
        return loaded_models
    
    def predict_fantasy_points(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Make fantasy points predictions"""
        try:
            if 'fantasy_points' not in self.models:
                return {'error': 'Fantasy points model not trained'}
            
            model = self.models['fantasy_points']
            scaler = self.scalers.get('fantasy_points')
            
            # Prepare features
            feature_columns = [col for col in features.columns 
                             if col not in ['player_id', 'game_id', 'game_date']]
            X = features[feature_columns].fillna(0)
            
            # Encode categorical variables
            for col in X.select_dtypes(include=['object']).columns:
                if col in self.encoders:
                    X[col] = self.encoders[col].transform(X[col].astype(str))
            
            # Scale features
            if scaler:
                X_scaled = scaler.transform(X)
            else:
                X_scaled = X.values
            
            # Make predictions
            predictions = model.predict(X_scaled)
            
            return {
                'predictions': predictions.tolist(),
                'model_confidence': 'high'  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return {'error': str(e)}

def main():
    """Test the ML model trainer"""
    logger.info("🧪 Testing ML Model Trainer...")
    
    # Create mock database
    class MockDatabase:
        def get_dataframe(self, query, params=None):
            # Return mock data for testing
            return pd.DataFrame({
                'player_id': [1, 2, 3, 1, 2, 3],
                'fantasy_points': [25.5, 18.2, 32.1, 28.3, 15.8, 29.7],
                'game_date': ['2024-01-15', '2024-01-15', '2024-01-15', '2024-01-16', '2024-01-16', '2024-01-16'],
                'primary_position': ['PG', 'SG', 'SF', 'PG', 'SG', 'SF'],
                'team_id': [1, 2, 3, 1, 2, 3],
                'opponent_team_id': [2, 1, 1, 3, 3, 2]
            })
    
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
    logger.info(f"Feature engineering test: {features.shape}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
NBA Fantasy Optimizer - Player ID Mapping Analysis
Analyzes player name variations and team correlations between data sources
"""

import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher
from collections import defaultdict
import logging
from typing import Dict, List, Tuple, Optional
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PlayerMappingAnalyzer:
    def __init__(self, historical_data_path: str = "historical_data"):
        self.historical_data_path = historical_data_path
        self.historical_players = None
        self.historical_teams = None
        self.mysportsfeeds_players = None
        self.mysportsfeeds_teams = None
        
    def load_historical_data(self):
        """Load historical player and team data"""
        logger.info("📊 Loading historical data...")
        
        try:
            # Load historical players
            self.historical_players = pd.read_csv(f"{self.historical_data_path}/player.csv")
            logger.info(f"✅ Loaded {len(self.historical_players)} historical players")
            
            # Load historical teams
            self.historical_teams = pd.read_csv(f"{self.historical_data_path}/team.csv")
            logger.info(f"✅ Loaded {len(self.historical_teams)} historical teams")
            
            # Load common player info for additional context
            common_player_info = pd.read_csv(f"{self.historical_data_path}/common_player_info.csv")
            logger.info(f"✅ Loaded {len(common_player_info)} common player info records")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error loading historical data: {e}")
            return False
    
    def load_mysportsfeeds_data(self):
        """Load MySportsFeeds data from API or database"""
        logger.info("📊 Loading MySportsFeeds data...")
        
        try:
            # For now, we'll create sample data structure
            # In production, this would come from the API or database
            self.mysportsfeeds_players = pd.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'firstName': ['LeBron', 'Stephen', 'Kevin', 'Giannis', 'Luka'],
                'lastName': ['James', 'Curry', 'Durant', 'Antetokounmpo', 'Doncic'],
                'position': ['SF', 'PG', 'SF', 'PF', 'PG'],
                'team': ['LAL', 'GSW', 'PHX', 'MIL', 'DAL']
            })
            
            self.mysportsfeeds_teams = pd.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'abbreviation': ['LAL', 'GSW', 'PHX', 'MIL', 'DAL'],
                'name': ['Lakers', 'Warriors', 'Suns', 'Bucks', 'Mavericks']
            })
            
            logger.info(f"✅ Loaded {len(self.mysportsfeeds_players)} MySportsFeeds players")
            logger.info(f"✅ Loaded {len(self.mysportsfeeds_teams)} MySportsFeeds teams")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error loading MySportsFeeds data: {e}")
            return False
    
    def normalize_name(self, name: str) -> str:
        """Normalize player names for better matching"""
        if pd.isna(name) or name == '':
            return ''
        
        # Convert to lowercase
        name = str(name).lower().strip()
        
        # Remove common suffixes and prefixes
        suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'v']
        for suffix in suffixes:
            if name.endswith(f' {suffix}'):
                name = name[:-len(f' {suffix}')]
        
        # Remove special characters and extra spaces
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        if not name1 or not name2:
            return 0.0
        
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use SequenceMatcher for similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity
    
    def analyze_name_patterns(self):
        """Analyze name patterns in historical data"""
        logger.info("🔍 Analyzing name patterns in historical data...")
        
        if self.historical_players is None:
            logger.error("❌ Historical players data not loaded")
            return None
        
        # Analyze name patterns
        name_analysis = {
            'total_players': len(self.historical_players),
            'name_variations': {},
            'common_patterns': [],
            'special_characters': [],
            'name_lengths': []
        }
        
        # Analyze first names
        first_names = self.historical_players['first_name'].dropna()
        name_analysis['first_name_patterns'] = {
            'count': len(first_names),
            'unique': first_names.nunique(),
            'most_common': first_names.value_counts().head(10).to_dict()
        }
        
        # Analyze last names
        last_names = self.historical_players['last_name'].dropna()
        name_analysis['last_name_patterns'] = {
            'count': len(last_names),
            'unique': last_names.nunique(),
            'most_common': last_names.value_counts().head(10).to_dict()
        }
        
        # Analyze full names
        full_names = self.historical_players['full_name'].dropna()
        name_analysis['full_name_patterns'] = {
            'count': len(full_names),
            'unique': full_names.nunique(),
            'most_common': full_names.value_counts().head(10).to_dict()
        }
        
        # Find names with special characters
        special_chars = []
        for name in full_names:
            if re.search(r'[^\w\s]', str(name)):
                special_chars.append(name)
        
        name_analysis['special_characters'] = special_chars[:20]  # First 20 examples
        
        # Analyze name lengths
        name_lengths = [len(str(name)) for name in full_names]
        name_analysis['name_lengths'] = {
            'min': min(name_lengths) if name_lengths else 0,
            'max': max(name_lengths) if name_lengths else 0,
            'mean': np.mean(name_lengths) if name_lengths else 0,
            'median': np.median(name_lengths) if name_lengths else 0
        }
        
        logger.info(f"✅ Name pattern analysis complete")
        return name_analysis
    
    def analyze_team_correlations(self):
        """Analyze team data for correlation mapping"""
        logger.info("🏀 Analyzing team correlations...")
        
        if self.historical_teams is None:
            logger.error("❌ Historical teams data not loaded")
            return None
        
        team_analysis = {
            'total_teams': len(self.historical_teams),
            'team_abbreviations': self.historical_teams['abbreviation'].tolist(),
            'team_names': self.historical_teams['full_name'].tolist(),
            'team_cities': self.historical_teams['city'].tolist()
        }
        
        logger.info(f"✅ Team correlation analysis complete")
        return team_analysis
    
    def create_mapping_strategy(self):
        """Create comprehensive mapping strategy"""
        logger.info("🎯 Creating player mapping strategy...")
        
        strategy = {
            'approach': 'Multi-layered matching with confidence scoring',
            'layers': [
                {
                    'name': 'Exact Name Match',
                    'description': 'Direct first_name + last_name match',
                    'confidence': 1.0,
                    'fallback': False
                },
                {
                    'name': 'Normalized Name Match',
                    'description': 'Normalized name matching (removes special chars, case insensitive)',
                    'confidence': 0.9,
                    'fallback': True
                },
                {
                    'name': 'Fuzzy Name Match',
                    'description': 'Fuzzy string matching with similarity threshold',
                    'confidence': 0.8,
                    'fallback': True
                },
                {
                    'name': 'Team + Name Match',
                    'description': 'Team correlation + name matching',
                    'confidence': 0.85,
                    'fallback': True
                },
                {
                    'name': 'Jersey Number + Team Match',
                    'description': 'Jersey number + team matching (if available)',
                    'confidence': 0.7,
                    'fallback': True
                }
            ],
            'confidence_thresholds': {
                'high_confidence': 0.9,
                'medium_confidence': 0.8,
                'low_confidence': 0.7,
                'manual_review': 0.6
            },
            'name_normalization': {
                'remove_special_chars': True,
                'case_insensitive': True,
                'remove_suffixes': ['jr', 'sr', 'ii', 'iii', 'iv', 'v'],
                'remove_prefixes': [],
                'handle_apostrophes': True
            },
            'team_matching': {
                'use_abbreviations': True,
                'use_full_names': True,
                'use_cities': True,
                'fuzzy_team_matching': True
            }
        }
        
        logger.info("✅ Mapping strategy created")
        return strategy
    
    def generate_mapping_report(self):
        """Generate comprehensive mapping analysis report"""
        logger.info("📋 Generating player mapping analysis report...")
        
        # Load data
        if not self.load_historical_data():
            return None
        
        if not self.load_mysportsfeeds_data():
            return None
        
        # Analyze patterns
        name_patterns = self.analyze_name_patterns()
        team_correlations = self.analyze_team_correlations()
        mapping_strategy = self.create_mapping_strategy()
        
        # Create comprehensive report
        report = {
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'data_sources': {
                'historical_players': len(self.historical_players) if self.historical_players is not None else 0,
                'historical_teams': len(self.historical_teams) if self.historical_teams is not None else 0,
                'mysportsfeeds_players': len(self.mysportsfeeds_players) if self.mysportsfeeds_players is not None else 0,
                'mysportsfeeds_teams': len(self.mysportsfeeds_teams) if self.mysportsfeeds_teams is not None else 0
            },
            'name_patterns': name_patterns,
            'team_correlations': team_correlations,
            'mapping_strategy': mapping_strategy,
            'recommendations': [
                "Use multi-layered matching approach with confidence scoring",
                "Implement name normalization for better matching",
                "Use team correlation as secondary matching criteria",
                "Create manual review process for low-confidence matches",
                "Build mapping table for future reference and updates"
            ]
        }
        
        # Save report
        with open('player_mapping_analysis.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info("✅ Mapping analysis report generated: player_mapping_analysis.json")
        return report

def main():
    """Main analysis function"""
    print("🔍 NBA Fantasy Optimizer - Player ID Mapping Analysis")
    print("=" * 60)
    
    analyzer = PlayerMappingAnalyzer()
    report = analyzer.generate_mapping_report()
    
    if report:
        print("\n📊 Analysis Summary:")
        print(f"   Historical Players: {report['data_sources']['historical_players']}")
        print(f"   Historical Teams: {report['data_sources']['historical_teams']}")
        print(f"   MySportsFeeds Players: {report['data_sources']['mysportsfeeds_players']}")
        print(f"   MySportsFeeds Teams: {report['data_sources']['mysportsfeeds_teams']}")
        
        print("\n🎯 Mapping Strategy:")
        for layer in report['mapping_strategy']['layers']:
            print(f"   • {layer['name']}: {layer['description']} (Confidence: {layer['confidence']})")
        
        print("\n📋 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        
        print(f"\n✅ Full report saved to: player_mapping_analysis.json")
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    main()

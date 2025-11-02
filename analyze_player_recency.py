#!/usr/bin/env python3
"""
NBA Fantasy Optimizer - Player Recency Analysis
Analyzes player activity timeframes to filter out old players
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_player_recency(historical_data_path: str = "historical_data"):
    """Analyze player recency in historical data"""
    logger.info("📊 Analyzing player recency in historical data...")
    
    try:
        # Load player data
        players_df = pd.read_csv(f"{historical_data_path}/player.csv")
        logger.info(f"✅ Loaded {len(players_df)} players")
        
        # Load common player info for additional context
        common_player_info = pd.read_csv(f"{historical_data_path}/common_player_info.csv")
        logger.info(f"✅ Loaded {len(common_player_info)} common player info records")
        
        # Analyze common player info for career years
        if 'from_year' in common_player_info.columns and 'to_year' in common_player_info.columns:
            # Filter out null values
            career_data = common_player_info[['person_id', 'first_name', 'last_name', 'from_year', 'to_year']].dropna()
            
            # Convert to numeric
            career_data['from_year'] = pd.to_numeric(career_data['from_year'], errors='coerce')
            career_data['to_year'] = pd.to_numeric(career_data['to_year'], errors='coerce')
            
            # Remove invalid years
            career_data = career_data.dropna()
            
            # Calculate career length
            career_data['career_length'] = career_data['to_year'] - career_data['from_year']
            
            # Get current year
            current_year = datetime.now().year
            
            # Calculate years since last played
            career_data['years_since_last_played'] = current_year - career_data['to_year']
            
            # Filter for players who played in last 5 years
            recent_players = career_data[career_data['years_since_last_played'] <= 5]
            
            # Analysis results
            analysis = {
                'total_players_with_career_data': len(career_data),
                'players_played_last_5_years': len(recent_players),
                'players_played_6_10_years_ago': len(career_data[(career_data['years_since_last_played'] > 5) & (career_data['years_since_last_played'] <= 10)]),
                'players_played_11_20_years_ago': len(career_data[(career_data['years_since_last_played'] > 10) & (career_data['years_since_last_played'] <= 20)]),
                'players_played_20_years_ago': len(career_data[career_data['years_since_last_played'] > 20]),
                'career_length_stats': {
                    'min': career_data['career_length'].min(),
                    'max': career_data['career_length'].max(),
                    'mean': career_data['career_length'].mean(),
                    'median': career_data['career_length'].median()
                },
                'years_since_last_played_stats': {
                    'min': career_data['years_since_last_played'].min(),
                    'max': career_data['years_since_last_played'].max(),
                    'mean': career_data['years_since_last_played'].mean(),
                    'median': career_data['years_since_last_played'].median()
                },
                'recent_players_sample': recent_players[['first_name', 'last_name', 'from_year', 'to_year', 'years_since_last_played']].head(10).to_dict('records'),
                'old_players_sample': career_data[career_data['years_since_last_played'] > 20][['first_name', 'last_name', 'from_year', 'to_year', 'years_since_last_played']].head(10).to_dict('records')
            }
            
            logger.info(f"✅ Recency analysis complete")
            return analysis
        else:
            logger.warning("⚠️ No career year data found in common_player_info")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error analyzing player recency: {e}")
        return None

def main():
    """Main analysis function"""
    print("🔍 NBA Fantasy Optimizer - Player Recency Analysis")
    print("=" * 60)
    
    analysis = analyze_player_recency()
    
    if analysis:
        print(f"\n📊 Player Recency Analysis:")
        print(f"   Total Players with Career Data: {analysis['total_players_with_career_data']}")
        print(f"   Players Played Last 5 Years: {analysis['players_played_last_5_years']}")
        print(f"   Players Played 6-10 Years Ago: {analysis['players_played_6_10_years_ago']}")
        print(f"   Players Played 11-20 Years Ago: {analysis['players_played_11_20_years_ago']}")
        print(f"   Players Played 20+ Years Ago: {analysis['players_played_20_years_ago']}")
        
        print(f"\n📈 Career Length Stats:")
        print(f"   Min: {analysis['career_length_stats']['min']} years")
        print(f"   Max: {analysis['career_length_stats']['max']} years")
        print(f"   Mean: {analysis['career_length_stats']['mean']:.1f} years")
        print(f"   Median: {analysis['career_length_stats']['median']:.1f} years")
        
        print(f"\n⏰ Years Since Last Played:")
        print(f"   Min: {analysis['years_since_last_played_stats']['min']} years")
        print(f"   Max: {analysis['years_since_last_played_stats']['max']} years")
        print(f"   Mean: {analysis['years_since_last_played_stats']['mean']:.1f} years")
        print(f"   Median: {analysis['years_since_last_played_stats']['median']:.1f} years")
        
        print(f"\n🏀 Recent Players Sample (Last 5 Years):")
        for player in analysis['recent_players_sample'][:5]:
            print(f"   • {player['first_name']} {player['last_name']} ({player['from_year']}-{player['to_year']}, {player['years_since_last_played']} years ago)")
        
        print(f"\n👴 Old Players Sample (20+ Years Ago):")
        for player in analysis['old_players_sample'][:5]:
            print(f"   • {player['first_name']} {player['last_name']} ({player['from_year']}-{player['to_year']}, {player['years_since_last_played']} years ago)")
        
        print(f"\n✅ Analysis complete!")
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    main()

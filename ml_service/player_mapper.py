"""
NBA Fantasy Optimizer - Player ID Mapping Service
Implements robust player mapping between historical data and MySportsFeeds
"""

import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class MatchConfidence(Enum):
    EXACT = 1.0
    HIGH = 0.9
    MEDIUM = 0.8
    LOW = 0.7
    MANUAL_REVIEW = 0.6

@dataclass
class PlayerMatch:
    historical_id: str
    mysportsfeeds_id: str
    confidence: float
    match_type: str
    historical_name: str
    mysportsfeeds_name: str
    team_correlation: bool
    notes: str = ""

class PlayerMapper:
    def __init__(self):
        self.historical_players = None
        self.historical_teams = None
        self.mysportsfeeds_players = None
        self.mysportsfeeds_teams = None
        self.mapping_table = None
        
    def load_historical_data(self, historical_data_path: str = "historical_data", years_threshold: int = 5):
        """Load historical player and team data with recency filter"""
        logger.info("📊 Loading historical data with recency filter...")
        
        try:
            # Load historical players
            self.historical_players = pd.read_csv(f"{historical_data_path}/player.csv")
            logger.info(f"✅ Loaded {len(self.historical_players)} historical players")
            
            # Load historical teams
            self.historical_teams = pd.read_csv(f"{historical_data_path}/team.csv")
            logger.info(f"✅ Loaded {len(self.historical_teams)} historical teams")
            
            # Load common player info for career data
            common_player_info = pd.read_csv(f"{historical_data_path}/common_player_info.csv")
            logger.info(f"✅ Loaded {len(common_player_info)} common player info records")
            
            # Apply recency filter
            if 'from_year' in common_player_info.columns and 'to_year' in common_player_info.columns:
                # Filter for players who played in last N years
                current_year = datetime.now().year
                common_player_info['from_year'] = pd.to_numeric(common_player_info['from_year'], errors='coerce')
                common_player_info['to_year'] = pd.to_numeric(common_player_info['to_year'], errors='coerce')
                
                # Remove invalid years and calculate years since last played
                valid_career_data = common_player_info.dropna(subset=['from_year', 'to_year'])
                valid_career_data['years_since_last_played'] = current_year - valid_career_data['to_year']
                
                # Filter for recent players
                recent_players = valid_career_data[valid_career_data['years_since_last_played'] <= years_threshold]
                
                # Get list of recent player IDs
                recent_player_ids = set(recent_players['person_id'].astype(str))
                
                # Filter historical players to only include recent ones
                original_count = len(self.historical_players)
                self.historical_players = self.historical_players[
                    self.historical_players['id'].astype(str).isin(recent_player_ids)
                ]
                
                logger.info(f"✅ Applied {years_threshold}-year recency filter:")
                logger.info(f"   Original players: {original_count}")
                logger.info(f"   Recent players: {len(self.historical_players)}")
                logger.info(f"   Filtered out: {original_count - len(self.historical_players)} old players")
            else:
                logger.warning("⚠️ No career year data found - no recency filter applied")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error loading historical data: {e}")
            return False
    
    def load_mysportsfeeds_data(self, mysportsfeeds_data: Dict):
        """Load MySportsFeeds data from API response"""
        logger.info("📊 Loading MySportsFeeds data...")
        
        try:
            # Convert API response to DataFrame
            if 'players' in mysportsfeeds_data:
                players_data = []
                for player in mysportsfeeds_data['players']:
                    players_data.append({
                        'id': player.get('id'),
                        'firstName': player.get('firstName', ''),
                        'lastName': player.get('lastName', ''),
                        'position': player.get('position', ''),
                        'team': player.get('currentTeam', {}).get('abbreviation', '') if player.get('currentTeam') else ''
                    })
                
                self.mysportsfeeds_players = pd.DataFrame(players_data)
                logger.info(f"✅ Loaded {len(self.mysportsfeeds_players)} MySportsFeeds players")
            
            if 'teams' in mysportsfeeds_data:
                teams_data = []
                for team in mysportsfeeds_data['teams']:
                    teams_data.append({
                        'id': team.get('id'),
                        'abbreviation': team.get('abbreviation', ''),
                        'name': team.get('name', ''),
                        'city': team.get('city', '')
                    })
                
                self.mysportsfeeds_teams = pd.DataFrame(teams_data)
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
    
    def exact_name_match(self, hist_player: pd.Series, msf_player: pd.Series) -> bool:
        """Check for exact name match"""
        hist_first = str(hist_player.get('first_name', '')).strip()
        hist_last = str(hist_player.get('last_name', '')).strip()
        msf_first = str(msf_player.get('firstName', '')).strip()
        msf_last = str(msf_player.get('lastName', '')).strip()
        
        return (hist_first.lower() == msf_first.lower() and 
                hist_last.lower() == msf_last.lower())
    
    def normalized_name_match(self, hist_player: pd.Series, msf_player: pd.Series) -> bool:
        """Check for normalized name match"""
        hist_first = self.normalize_name(hist_player.get('first_name', ''))
        hist_last = self.normalize_name(hist_player.get('last_name', ''))
        msf_first = self.normalize_name(msf_player.get('firstName', ''))
        msf_last = self.normalize_name(msf_player.get('lastName', ''))
        
        return (hist_first == msf_first and hist_last == msf_last)
    
    def fuzzy_name_match(self, hist_player: pd.Series, msf_player: pd.Series, threshold: float = 0.8) -> Tuple[bool, float]:
        """Check for fuzzy name match with similarity score"""
        hist_first = str(hist_player.get('first_name', ''))
        hist_last = str(hist_player.get('last_name', ''))
        msf_first = str(msf_player.get('firstName', ''))
        msf_last = str(msf_player.get('lastName', ''))
        
        # Calculate similarity for first and last names
        first_sim = self.calculate_name_similarity(hist_first, msf_first)
        last_sim = self.calculate_name_similarity(hist_last, msf_last)
        
        # Average similarity
        avg_similarity = (first_sim + last_sim) / 2
        
        return avg_similarity >= threshold, avg_similarity
    
    def team_correlation_match(self, hist_player: pd.Series, msf_player: pd.Series) -> bool:
        """Check for team correlation match"""
        # This would require team mapping logic
        # For now, return False as placeholder
        return False
    
    def find_matches(self, confidence_threshold: float = 0.7) -> List[PlayerMatch]:
        """Find matches between historical and MySportsFeeds players"""
        logger.info("🔍 Finding player matches...")
        
        if self.historical_players is None or self.mysportsfeeds_players is None:
            logger.error("❌ Data not loaded")
            return []
        
        matches = []
        
        for _, hist_player in self.historical_players.iterrows():
            best_match = None
            best_confidence = 0.0
            best_match_type = ""
            
            for _, msf_player in self.mysportsfeeds_players.iterrows():
                # Try exact match first
                if self.exact_name_match(hist_player, msf_player):
                    best_match = msf_player
                    best_confidence = MatchConfidence.EXACT.value
                    best_match_type = "Exact Name Match"
                    break
                
                # Try normalized match
                elif self.normalized_name_match(hist_player, msf_player):
                    if MatchConfidence.HIGH.value > best_confidence:
                        best_match = msf_player
                        best_confidence = MatchConfidence.HIGH.value
                        best_match_type = "Normalized Name Match"
                
                # Try fuzzy match
                elif self.fuzzy_name_match(hist_player, msf_player)[0]:
                    fuzzy_sim = self.fuzzy_name_match(hist_player, msf_player)[1]
                    if fuzzy_sim > best_confidence:
                        best_match = msf_player
                        best_confidence = fuzzy_sim
                        best_match_type = "Fuzzy Name Match"
            
            # Create match if confidence is above threshold
            if best_match is not None and best_confidence >= confidence_threshold:
                match = PlayerMatch(
                    historical_id=str(hist_player.get('id', '')),
                    mysportsfeeds_id=str(best_match.get('id', '')),
                    confidence=best_confidence,
                    match_type=best_match_type,
                    historical_name=f"{hist_player.get('first_name', '')} {hist_player.get('last_name', '')}",
                    mysportsfeeds_name=f"{best_match.get('firstName', '')} {best_match.get('lastName', '')}",
                    team_correlation=False,  # Placeholder
                    notes=f"Matched via {best_match_type}"
                )
                matches.append(match)
        
        logger.info(f"✅ Found {len(matches)} matches above confidence threshold {confidence_threshold}")
        return matches
    
    def create_mapping_table(self, matches: List[PlayerMatch]) -> pd.DataFrame:
        """Create mapping table from matches"""
        logger.info("📋 Creating mapping table...")
        
        mapping_data = []
        for match in matches:
            mapping_data.append({
                'historical_id': match.historical_id,
                'mysportsfeeds_id': match.mysportsfeeds_id,
                'confidence': match.confidence,
                'match_type': match.match_type,
                'historical_name': match.historical_name,
                'mysportsfeeds_name': match.mysportsfeeds_name,
                'team_correlation': match.team_correlation,
                'notes': match.notes
            })
        
        self.mapping_table = pd.DataFrame(mapping_data)
        logger.info(f"✅ Created mapping table with {len(self.mapping_table)} entries")
        return self.mapping_table
    
    def save_mapping_table(self, filepath: str = "player_mapping.csv"):
        """Save mapping table to CSV"""
        if self.mapping_table is not None:
            self.mapping_table.to_csv(filepath, index=False)
            logger.info(f"✅ Mapping table saved to {filepath}")
        else:
            logger.error("❌ No mapping table to save")
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get summary of mapping results"""
        if self.mapping_table is None:
            return {"error": "No mapping table available"}
        
        summary = {
            "total_matches": len(self.mapping_table),
            "confidence_distribution": self.mapping_table['confidence'].value_counts().to_dict(),
            "match_type_distribution": self.mapping_table['match_type'].value_counts().to_dict(),
            "high_confidence_matches": len(self.mapping_table[self.mapping_table['confidence'] >= 0.9]),
            "medium_confidence_matches": len(self.mapping_table[(self.mapping_table['confidence'] >= 0.8) & (self.mapping_table['confidence'] < 0.9)]),
            "low_confidence_matches": len(self.mapping_table[(self.mapping_table['confidence'] >= 0.7) & (self.mapping_table['confidence'] < 0.8)]),
            "manual_review_needed": len(self.mapping_table[self.mapping_table['confidence'] < 0.7])
        }
        
        return summary

def main():
    """Main function for testing player mapping"""
    print("🔍 NBA Fantasy Optimizer - Player Mapping Service")
    print("=" * 60)
    
    mapper = PlayerMapper()
    
    # Load historical data
    if not mapper.load_historical_data():
        print("❌ Failed to load historical data")
        return
    
    # Create sample MySportsFeeds data for testing
    sample_msf_data = {
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
    
    # Load MySportsFeeds data
    if not mapper.load_mysportsfeeds_data(sample_msf_data):
        print("❌ Failed to load MySportsFeeds data")
        return
    
    # Find matches
    matches = mapper.find_matches(confidence_threshold=0.7)
    
    # Create mapping table
    mapping_table = mapper.create_mapping_table(matches)
    
    # Get summary
    summary = mapper.get_mapping_summary()
    
    print(f"\n📊 Mapping Summary:")
    print(f"   Total Matches: {summary['total_matches']}")
    print(f"   High Confidence: {summary['high_confidence_matches']}")
    print(f"   Medium Confidence: {summary['medium_confidence_matches']}")
    print(f"   Low Confidence: {summary['low_confidence_matches']}")
    print(f"   Manual Review: {summary['manual_review_needed']}")
    
    # Save mapping table
    mapper.save_mapping_table()
    
    print(f"\n✅ Player mapping complete!")

if __name__ == "__main__":
    main()

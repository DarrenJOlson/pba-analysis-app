import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os

class PBAAnalyzer:
    def __init__(self, data_path="data/combined_pba_data.csv"):
        """
        Initialize with path to combined PBA data
        """
        print(f"Loading data from {data_path}...")
        self.df = pd.read_csv(data_path)
        self._preprocess_data()
        
    def _preprocess_data(self):
        """
        Preprocess data for analysis
        """
        print("Preprocessing data...")
        
        # Convert dates to datetime
        for date_col in ['start_date', 'end_date']:
            if date_col in self.df.columns:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                # Make datetime timezone-naive to avoid comparison issues
                if not self.df[date_col].empty and pd.notna(self.df[date_col].iloc[0]):
                    if hasattr(self.df[date_col].iloc[0], 'tz'):
                        self.df[date_col] = self.df[date_col].dt.tz_localize(None)
        
        # Convert position to numeric
        if 'position' in self.df.columns:
            self.df['position'] = pd.to_numeric(self.df['position'], errors='coerce')
        
        # Convert earnings to numeric
        if 'earnings' in self.df.columns:
            self.df['earnings'] = pd.to_numeric(self.df['earnings'], errors='coerce')
        
        # Convert average to numeric, properly handling missing values
        if 'average' in self.df.columns:
            # Replace blank/empty strings with NaN
            self.df['average'] = self.df['average'].replace('', np.nan)
            # Convert to numeric, coercing errors to NaN
            self.df['average'] = pd.to_numeric(self.df['average'], errors='coerce')
            
        # Clean up match play record
        if 'match_play_record' in self.df.columns:
            # Replace blank/empty strings with NaN
            self.df['match_play_record'] = self.df['match_play_record'].replace('', np.nan)
            # Remove quotes
            self.df['match_play_record'] = self.df['match_play_record'].str.replace("'", "")
            
            # Extract wins, losses, ties from match play record
            mp_parts = self.df['match_play_record'].str.extract(r'(\d+)-(\d+)-(\d+)')
            if not mp_parts.empty and not mp_parts.isnull().all().all():
                self.df['mp_wins'] = pd.to_numeric(mp_parts[0], errors='coerce')
                self.df['mp_losses'] = pd.to_numeric(mp_parts[1], errors='coerce')
                self.df['mp_ties'] = pd.to_numeric(mp_parts[2], errors='coerce')
                
                # Calculate win percentage, handle missing values
                total_matches = self.df['mp_wins'].fillna(0) + self.df['mp_losses'].fillna(0) + self.df['mp_ties'].fillna(0)
                self.df['win_percentage'] = np.where(total_matches > 0, self.df['mp_wins'] / total_matches * 100, np.nan)
        
        # Convert pattern length to numeric
        if 'pattern_length' in self.df.columns:
            self.df['pattern_length'] = pd.to_numeric(self.df['pattern_length'], errors='coerce')
            
            # Create pattern categories based on length
            self.df['pattern_category'] = pd.cut(
                self.df['pattern_length'],
                bins=[0, 36, 41, 47, 100],
                labels=['Short', 'Medium', 'Long', 'Extra Long']
            )
            
        # Add a timestamp field for recency calculations - ensure timezone-naive
        self.df['timestamp'] = self.df['start_date']
        if not self.df['timestamp'].empty and pd.notna(self.df['timestamp'].iloc[0]):
            if hasattr(self.df['timestamp'].iloc[0], 'tz'):
                self.df['timestamp'] = self.df['timestamp'].dt.tz_localize(None)
        
        # Add a flag for major tournaments (higher prestige events)
        major_keywords = ['major', 'championship', 'open', 'masters', 'tournament of champions', 'players']
        self.df['is_major'] = self.df['tournament_name'].str.lower().apply(
            lambda x: any(keyword in x.lower() for keyword in major_keywords) if isinstance(x, str) else False
        )
        
        print("Preprocessing complete.")
        print(f"Dataset contains {len(self.df)} results across {self.df['tournament_name'].nunique()} tournaments")
        
        # Print pattern distributions
        pattern_counts = self.df.groupby('pattern_name').size().sort_values(ascending=False)
        if len(pattern_counts) > 0:
            print("Top patterns in dataset:")
            for pattern, count in pattern_counts.head(5).items():
                print(f"  {pattern}: {count} results")
        
    def get_bowler_overall_stats(self, min_tournaments=1, recency_months=None):
        """
        Get overall stats for all bowlers
        """
        # Filter by recency if needed
        if recency_months:
            now = datetime.now()
            cutoff_date = now - timedelta(days=30*recency_months)
            df = self.df[self.df['timestamp'] >= cutoff_date].copy()
            print(f"Using data from the last {recency_months} months ({len(df)} results)")
        else:
            df = self.df.copy()
            print(f"Using all available data ({len(df)} results)")
            
        # Group by bowler name and calculate stats
        stats = df.groupby('name').agg({
            'tournament_name': 'count',
            'position': ['mean', 'min', 'median'],
            'earnings': ['sum', 'mean']
        })
        
        # Clean up column names
        stats.columns = [
            'tournaments_played',
            'avg_position',
            'best_position',
            'median_position',
            'total_earnings',
            'avg_earnings'
        ]
        
        # Calculate percentage of tournaments in the top 5
        top5_counts = df[df['position'] <= 5].groupby('name').size()
        # Merge with stats
        if not top5_counts.empty:
            stats = stats.join(top5_counts.rename('top5_finishes'), how='left')
            stats['top5_percentage'] = (stats['top5_finishes'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['top5_finishes'] = 0
            stats['top5_percentage'] = 0
        
        # Calculate wins (position = 1)
        win_counts = df[df['position'] == 1].groupby('name').size()
        # Merge with stats
        if not win_counts.empty:
            stats = stats.join(win_counts.rename('wins'), how='left')
            stats['win_percentage'] = (stats['wins'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['wins'] = 0
            stats['win_percentage'] = 0
            
        # Filter by minimum tournaments if needed
        if min_tournaments > 0:
            stats = stats[stats['tournaments_played'] >= min_tournaments]
            
        return stats

    def get_bowler_stats(self, min_tournaments=1, recency_months=None):
        """
        Get overall stats for all bowlers
        Alias for get_bowler_overall_stats for API compatibility
        """
        return self.get_bowler_overall_stats(min_tournaments, recency_months)

    def get_specific_pattern_stats(self, pattern_name, min_tournaments=0, recency_months=None):
        """
        Get bowler stats on a specific pattern
        """
        # Filter by pattern name (case-insensitive)
        pattern_df = self.df[self.df['pattern_name'].str.lower() == pattern_name.lower()].copy()
        
        if len(pattern_df) == 0:
            # Try partial matching
            print(f"No exact matches for pattern '{pattern_name}'. Checking similar names...")
            pattern_df = self.df[self.df['pattern_name'].str.lower().str.contains(pattern_name.lower(), na=False)]
            
            if len(pattern_df) == 0:
                print(f"No similar patterns found for '{pattern_name}'")
                return pd.DataFrame()
                
            # Get unique pattern names that matched
            pattern_names = pattern_df['pattern_name'].unique()
            print(f"Found {len(pattern_names)} similar pattern names:")
            for name in pattern_names:
                print(f"  {name}")
                
            # Use the most common match
            most_common = pattern_df['pattern_name'].value_counts().index[0]
            pattern_df = self.df[self.df['pattern_name'] == most_common].copy()
            print(f"Using most common match: {most_common}")
            
        # Filter by recency if needed
        if recency_months:
            now = datetime.now()
            cutoff_date = now - timedelta(days=30*recency_months)
            # Make sure timestamps are timezone-naive
            if not pattern_df['timestamp'].empty and pd.notna(pattern_df['timestamp'].iloc[0]):
                if hasattr(pattern_df['timestamp'].iloc[0], 'tz'):
                    pattern_df.loc[:, 'timestamp'] = pattern_df['timestamp'].dt.tz_localize(None)
                    
            recent_df = pattern_df[pattern_df['timestamp'] >= cutoff_date]
            if len(recent_df) > 0:
                pattern_df = recent_df
                print(f"Using {len(pattern_df)} results from the last {recency_months} months")
            else:
                print(f"No recent data (last {recency_months} months) for this pattern. Using all available data.")
        else:
            print(f"Using all available data for pattern ({len(pattern_df)} results)")
        
        print(f"Found {len(pattern_df)} results for pattern across {pattern_df['tournament_name'].nunique()} tournaments")
            
        # Group by bowler and compute stats
        stats = pattern_df.groupby('name').agg({
            'tournament_name': 'count',
            'position': ['mean', 'min'],
            'earnings': ['sum', 'mean']
        })
        
        # Clean up column names
        stats.columns = [
            'tournaments_played',
            'avg_position',
            'best_position',
            'total_earnings',
            'avg_earnings'
        ]
        
        # Calculate top 5 finishes
        top5_counts = pattern_df[pattern_df['position'] <= 5].groupby('name').size()
        if not top5_counts.empty:
            stats = stats.join(top5_counts.rename('top5_finishes'), how='left')
            stats['top5_percentage'] = (stats['top5_finishes'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['top5_finishes'] = 0
            stats['top5_percentage'] = 0
            
        # Calculate wins
        win_counts = pattern_df[pattern_df['position'] == 1].groupby('name').size()
        if not win_counts.empty:
            stats = stats.join(win_counts.rename('wins'), how='left')
            stats['win_percentage'] = (stats['wins'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['wins'] = 0
            stats['win_percentage'] = 0
            
        # Filter by minimum tournaments if specified
        if min_tournaments > 0:
            stats = stats[stats['tournaments_played'] >= min_tournaments]
            
        return stats

    def get_pattern_length_stats(self, length, length_range=2, min_tournaments=0, recency_months=None):
        """
        Get bowler stats on patterns of a specific length (plus/minus range)
        """
        # Ensure length is numeric
        if length is None:
            print(f"No pattern length specified")
            return pd.DataFrame()
            
        try:
            length = float(length)  # Convert to float to match dataframe dtype
            length_min = length - length_range
            length_max = length + length_range
        except (ValueError, TypeError):
            print(f"Invalid pattern length: {length}")
            return pd.DataFrame()
        
        print(f"Looking for patterns between {length_min}-{length_max} feet")
        
        # Filter by pattern length (within range) - ensuring pattern_length is numeric
        pattern_df = self.df[
            self.df['pattern_length'].notna() &  # Only consider rows with pattern length
            (self.df['pattern_length'].astype(float) >= length_min) & 
            (self.df['pattern_length'].astype(float) <= length_max)
        ].copy()
        
        if len(pattern_df) == 0:
            print(f"No data found for patterns between {length_min}-{length_max} feet")
            return pd.DataFrame()
            
        # Filter by recency if needed
        if recency_months:
            now = datetime.now()
            cutoff_date = now - timedelta(days=30*recency_months)
            # Make sure timestamps are timezone-naive
            if not pattern_df['timestamp'].empty and pd.notna(pattern_df['timestamp'].iloc[0]):
                if hasattr(pattern_df['timestamp'].iloc[0], 'tz'):
                    pattern_df.loc[:, 'timestamp'] = pattern_df['timestamp'].dt.tz_localize(None)
                    
            recent_df = pattern_df[pattern_df['timestamp'] >= cutoff_date]
            if len(recent_df) > 0:
                pattern_df = recent_df
                print(f"Using {len(pattern_df)} results from the last {recency_months} months")
            else:
                print(f"No recent data (last {recency_months} months) for this length. Using all available data.")
        else:
            print(f"Using all available data for pattern length ({len(pattern_df)} results)")
                
        print(f"Found {len(pattern_df)} results for {length}±{length_range}ft patterns across {pattern_df['tournament_name'].nunique()} tournaments")
        
        # Show breakdown of pattern lengths found
        length_counts = pattern_df['pattern_length'].value_counts().sort_index()
        print("Pattern length breakdown:")
        for pattern_len, count in length_counts.items():
            print(f"  {pattern_len}ft: {count} results")
            
        # Group by bowler and compute stats
        stats = pattern_df.groupby('name').agg({
            'tournament_name': 'count',
            'position': ['mean', 'min'],
            'earnings': ['sum', 'mean']
        })
        
        # Clean up column names
        stats.columns = [
            'tournaments_played',
            'avg_position',
            'best_position',
            'total_earnings',
            'avg_earnings'
        ]
        
        # Calculate top 5 finishes
        top5_counts = pattern_df[pattern_df['position'] <= 5].groupby('name').size()
        if not top5_counts.empty:
            stats = stats.join(top5_counts.rename('top5_finishes'), how='left')
            stats['top5_percentage'] = (stats['top5_finishes'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['top5_finishes'] = 0
            stats['top5_percentage'] = 0
            
        # Calculate wins
        win_counts = pattern_df[pattern_df['position'] == 1].groupby('name').size()
        if not win_counts.empty:
            stats = stats.join(win_counts.rename('wins'), how='left')
            stats['win_percentage'] = (stats['wins'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['wins'] = 0
            stats['win_percentage'] = 0
            
        # Filter by minimum tournaments if specified
        if min_tournaments > 0:
            stats = stats[stats['tournaments_played'] >= min_tournaments]
            
        return stats
    
    def get_center_stats(self, center_name, min_tournaments=0, recency_months=None):
        """
        Get bowler stats at a specific bowling center
        """
        # Filter by center name (partial match, case-insensitive)
        center_df = self.df[self.df['center_name'].str.contains(center_name, case=False, na=False)].copy()
        
        if len(center_df) == 0:
            print(f"No data found for center containing '{center_name}'")
            return pd.DataFrame()
            
        # Check which centers matched
        centers = center_df['center_name'].unique()
        if len(centers) > 1:
            print(f"Found {len(centers)} matching centers:")
            for center in centers:
                count = len(center_df[center_df['center_name'] == center])
                print(f"  {center}: {count} results")
                
        # Filter by recency if needed
        if recency_months:
            now = datetime.now()
            cutoff_date = now - timedelta(days=30*recency_months)
            # Make sure timestamps are timezone-naive
            if not center_df['timestamp'].empty and pd.notna(center_df['timestamp'].iloc[0]):
                if hasattr(center_df['timestamp'].iloc[0], 'tz'):
                    center_df.loc[:, 'timestamp'] = center_df['timestamp'].dt.tz_localize(None)
                    
            recent_df = center_df[center_df['timestamp'] >= cutoff_date]
            if len(recent_df) > 0:
                center_df = recent_df
                print(f"Using {len(center_df)} results from the last {recency_months} months")
            else:
                print(f"No recent data (last {recency_months} months) for this center. Using all available data.")
        else:
            print(f"Using all available data for center ({len(center_df)} results)")
                
        print(f"Found {len(center_df)} results at '{center_name}' across {center_df['tournament_name'].nunique()} tournaments")
            
        # Group by bowler and compute stats
        stats = center_df.groupby('name').agg({
            'tournament_name': 'count',
            'position': ['mean', 'min'],
            'earnings': ['sum', 'mean']
        })
        
        # Clean up column names
        stats.columns = [
            'tournaments_played',
            'avg_position',
            'best_position',
            'total_earnings',
            'avg_earnings'
        ]
        
        # Calculate top 5 finishes
        top5_counts = center_df[center_df['position'] <= 5].groupby('name').size()
        if not top5_counts.empty:
            stats = stats.join(top5_counts.rename('top5_finishes'), how='left')
            stats['top5_percentage'] = (stats['top5_finishes'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['top5_finishes'] = 0
            stats['top5_percentage'] = 0
            
        # Calculate wins
        win_counts = center_df[center_df['position'] == 1].groupby('name').size()
        if not win_counts.empty:
            stats = stats.join(win_counts.rename('wins'), how='left')
            stats['win_percentage'] = (stats['wins'] / stats['tournaments_played'] * 100).fillna(0)
        else:
            stats['wins'] = 0
            stats['win_percentage'] = 0
            
        # Filter by minimum tournaments if specified
        if min_tournaments > 0:
            stats = stats[stats['tournaments_played'] >= min_tournaments]
            
        return stats
    
    def normalize_position_stat(self, stat_series, reverse=True):
        """
        Normalize a position statistic to 0-100 scale
        For position, lower is better, so we reverse by default
        """
        if stat_series.empty or stat_series.isna().all():
            return pd.Series([50.0] * len(stat_series), index=stat_series.index)
            
        min_val = stat_series.min()
        max_val = stat_series.max()
        
        # Avoid division by zero
        if min_val == max_val:
            return pd.Series([50.0] * len(stat_series), index=stat_series.index)
            
        # Normalize to 0-100 scale
        if reverse:
            # For position, lower is better, so reverse the scale
            normalized = 100.0 - ((stat_series - min_val) / (max_val - min_val) * 100.0)
        else:
            # For other stats like earnings, higher is better
            normalized = (stat_series - min_val) / (max_val - min_val) * 100.0
        
        # Return as float series to maintain consistent data types
        return normalized.astype(float)
    
    def get_multi_factor_prediction(self, pattern_name=None, pattern_length=None, center_name=None, 
                                   recency_months=None, min_events_overall=3, top_n=20):
        """
        Get a multi-factor prediction for a tournament with weighted factors:
        - Specific pattern performance (highest weight)
        - Center performance (highest weight)
        - Similar length pattern performance (medium weight)
        - Overall performance (lowest weight)
        """
        print("\n===== MULTI-FACTOR TOURNAMENT PREDICTION =====")
        
        # 1. Get performance on the specific pattern (highest weight)
        pattern_stats = pd.DataFrame()
        pattern_length_value = None
        if pattern_name:
            pattern_stats = self.get_specific_pattern_stats(
                pattern_name, 
                min_tournaments=0,
                recency_months=recency_months
            )
            
            # Get pattern length if available
            if not pattern_stats.empty:
                pattern_rows = self.df[self.df['pattern_name'].str.lower() == pattern_name.lower()]
                if not pattern_rows.empty and pd.notna(pattern_rows['pattern_length'].iloc[0]):
                    pattern_length_value = float(pattern_rows['pattern_length'].iloc[0])
                    print(f"Pattern length: {pattern_length_value}ft")
                    
        elif pattern_length:
            # Use the pattern_length parameter instead
            try:
                pattern_length_value = float(pattern_length)
                print(f"Using pattern length: {pattern_length_value}ft")
            except (ValueError, TypeError):
                print(f"Invalid pattern length: {pattern_length}")
                pattern_length_value = None
        
        # 2. Get center performance (highest weight)
        center_stats = pd.DataFrame()
        if center_name:
            center_stats = self.get_center_stats(
                center_name,
                min_tournaments=0,
                recency_months=recency_months
            )
        
        # 3. Get similar length pattern performance (medium weight)
        length_stats = pd.DataFrame()
        if pattern_length_value:
            # Use a larger range (3 feet) to ensure we find similar patterns
            length_stats = self.get_pattern_length_stats(
                pattern_length_value,
                length_range=3,  # +/- 3 feet (more inclusive)
                min_tournaments=0,
                recency_months=recency_months
            )
            
        # 4. Get overall performance (lowest weight)
        overall_stats = self.get_bowler_overall_stats(
            min_tournaments=min_events_overall,
            recency_months=recency_months
        )
        
        print(f"\nFound data for: {len(pattern_stats)} bowlers on pattern, {len(center_stats)} bowlers at center, "
              f"{len(length_stats)} bowlers on similar length, {len(overall_stats)} bowlers overall")
        
        # Create a comprehensive bowler list from all sources
        all_bowlers = set()
        for stats_df in [pattern_stats, center_stats, length_stats, overall_stats]:
            if not stats_df.empty:
                all_bowlers.update(stats_df.index)
        
        all_bowlers = list(all_bowlers)
        print(f"Analyzing {len(all_bowlers)} total bowlers")
        
        # Create prediction dataframe with properly initialized columns
        predictions = pd.DataFrame(index=all_bowlers)
        
        # Add tournament counts for each factor
        predictions['pattern_tournaments'] = 0
        if not pattern_stats.empty:
            for idx in pattern_stats.index:
                if idx in predictions.index:
                    predictions.at[idx, 'pattern_tournaments'] = int(pattern_stats.at[idx, 'tournaments_played'])
        
        predictions['center_tournaments'] = 0
        if not center_stats.empty:
            for idx in center_stats.index:
                if idx in predictions.index:
                    predictions.at[idx, 'center_tournaments'] = int(center_stats.at[idx, 'tournaments_played'])
        
        predictions['length_tournaments'] = 0
        if not length_stats.empty:
            for idx in length_stats.index:
                if idx in predictions.index:
                    predictions.at[idx, 'length_tournaments'] = int(length_stats.at[idx, 'tournaments_played'])
        
        predictions['overall_tournaments'] = 0
        for idx in overall_stats.index:
            if idx in predictions.index:
                predictions.at[idx, 'overall_tournaments'] = int(overall_stats.at[idx, 'tournaments_played'])
        
        # Add position stats for each factor (these will be normalized later)
        predictions['pattern_position'] = np.nan  # Use NaN instead of 999
        if not pattern_stats.empty:
            for idx in pattern_stats.index:
                if idx in predictions.index:
                    predictions.at[idx, 'pattern_position'] = float(pattern_stats.at[idx, 'avg_position'])
        
        predictions['center_position'] = np.nan
        if not center_stats.empty:
            for idx in center_stats.index:
                if idx in predictions.index:
                    predictions.at[idx, 'center_position'] = float(center_stats.at[idx, 'avg_position'])
        
        predictions['length_position'] = np.nan
        if not length_stats.empty:
            for idx in length_stats.index:
                if idx in predictions.index:
                    predictions.at[idx, 'length_position'] = float(length_stats.at[idx, 'avg_position'])
        
        predictions['overall_position'] = np.nan
        for idx in overall_stats.index:
            if idx in predictions.index:
                predictions.at[idx, 'overall_position'] = float(overall_stats.at[idx, 'avg_position'])
        
        # Calculate experience factors (more experience = more reliable prediction)
        max_pattern = predictions['pattern_tournaments'].max() if predictions['pattern_tournaments'].max() > 0 else 1
        max_center = predictions['center_tournaments'].max() if predictions['center_tournaments'].max() > 0 else 1
        max_length = predictions['length_tournaments'].max() if predictions['length_tournaments'].max() > 0 else 1
        max_overall = predictions['overall_tournaments'].max() if predictions['overall_tournaments'].max() > 0 else 1
        
        predictions['pattern_exp'] = predictions['pattern_tournaments'] / max_pattern
        predictions['center_exp'] = predictions['center_tournaments'] / max_center
        predictions['length_exp'] = predictions['length_tournaments'] / max_length
        predictions['overall_exp'] = predictions['overall_tournaments'] / max_overall
        
        # Normalize scores, handling NaN values
        if not predictions['pattern_position'].dropna().empty:
            predictions['pattern_score'] = self.normalize_position_stat(predictions['pattern_position'].dropna())
        else:
            predictions['pattern_score'] = pd.Series(0.0, index=predictions.index)
            
        if not predictions['center_position'].dropna().empty:
            predictions['center_score'] = self.normalize_position_stat(predictions['center_position'].dropna())
        else:
            predictions['center_score'] = pd.Series(0.0, index=predictions.index)
            
        if not predictions['length_position'].dropna().empty:
            predictions['length_score'] = self.normalize_position_stat(predictions['length_position'].dropna())
        else:
            predictions['length_score'] = pd.Series(0.0, index=predictions.index)
            
        if not predictions['overall_position'].dropna().empty:
            predictions['overall_score'] = self.normalize_position_stat(predictions['overall_position'].dropna())
        else:
            predictions['overall_score'] = pd.Series(0.0, index=predictions.index)
        
        # Fill NaN values in scores with 0
        for col in ['pattern_score', 'center_score', 'length_score', 'overall_score']:
            predictions[col] = predictions[col].fillna(0.0)
        
        # Apply weights to each factor
        weights = {
            'pattern': 0.35,  # 35% pattern
            'center': 0.35,   # 35% center
            'length': 0.20,   # 20% similar length
            'overall': 0.10   # 10% overall
        }
        
        # Calculate weighted scores based on experience
        # If a bowler has no experience in a category, that weight is redistributed
        predictions['weighted_pattern'] = predictions['pattern_score'] * predictions['pattern_exp'] * weights['pattern']
        predictions['weighted_center'] = predictions['center_score'] * predictions['center_exp'] * weights['center']
        predictions['weighted_length'] = predictions['length_score'] * predictions['length_exp'] * weights['length']
        predictions['weighted_overall'] = predictions['overall_score'] * weights['overall']  # Always have overall data
        
        # Get total applied weight
        predictions['total_weight'] = (
            (predictions['pattern_exp'] > 0) * weights['pattern'] +
            (predictions['center_exp'] > 0) * weights['center'] +
            (predictions['length_exp'] > 0) * weights['length'] +
            weights['overall']  # Always include overall weight
        )
        
        # Total score normalized by applied weights
        predictions['total_score'] = (
            predictions['weighted_pattern'] + 
            predictions['weighted_center'] + 
            predictions['weighted_length'] + 
            predictions['weighted_overall']
        ) / predictions['total_weight'].replace(0, 1.0)  # Avoid division by zero
        
        # Clean up NaN values (if a bowler has no data in any category)
        predictions = predictions.fillna(0.0)
        
        # Filter bowlers with sufficient overall tournaments
        min_tournaments = min_events_overall
        predictions = predictions[predictions['overall_tournaments'] >= min_tournaments]
        
        if len(predictions) == 0:
            print(f"No bowlers with at least {min_tournaments} tournaments")
            return None
        
        # Calculate a confidence score based on data availability
        predictions['confidence'] = (
            predictions['pattern_exp'] * weights['pattern'] +
            predictions['center_exp'] * weights['center'] +
            predictions['length_exp'] * weights['length'] +
            (predictions['overall_exp'] * weights['overall'])
        ) / sum(weights.values())
        
        # Sort by total score
        predictions = predictions.sort_values('total_score', ascending=False)
        
        # Add rank and reset index
        predictions = predictions.reset_index()
        predictions.rename(columns={'index': 'name'}, inplace=True)
        predictions.insert(0, 'rank', range(1, len(predictions) + 1))
        
        # Get only top N predictions
        top_predictions = predictions.head(top_n)
        
        # Prepare clean output for display
        display_columns = [
            'rank', 'name', 
            'overall_position', 'overall_tournaments',
            'pattern_position', 'pattern_tournaments',
            'length_position', 'length_tournaments',
            'center_position', 'center_tournaments',
            'total_score', 'confidence'
        ]
        
        # Get top 5 percentages if available
        if not pattern_stats.empty:
            top_predictions['pattern_top5'] = np.nan
            for name in top_predictions['name']:
                if name in pattern_stats.index:
                    idx = top_predictions.index[top_predictions['name'] == name][0]
                    top_predictions.loc[idx, 'pattern_top5'] = pattern_stats.loc[name, 'top5_percentage']
        
        if not center_stats.empty:
            top_predictions['center_top5'] = np.nan
            for name in top_predictions['name']:
                if name in center_stats.index:
                    idx = top_predictions.index[top_predictions['name'] == name][0]
                    top_predictions.loc[idx, 'center_top5'] = center_stats.loc[name, 'top5_percentage']
            
        result = top_predictions[display_columns].copy()
        
        # Round numeric columns
        numeric_cols = result.select_dtypes(include=['float64']).columns
        result[numeric_cols] = result[numeric_cols].round(2)
        
        # Format for display
        print(f"\nTop {top_n} Bowlers - Multi-Factor Prediction:")
        print("-" * 100)
        
        for _, row in result.iterrows():
            overall_position = f"{row['overall_position']:5.2f}" if not pd.isna(row['overall_position']) else "  N/A"
            pattern_position = f"{row['pattern_position']:5.2f}" if not pd.isna(row['pattern_position']) else "  N/A"
            center_position = f"{row['center_position']:5.2f}" if not pd.isna(row['center_position']) else "  N/A"
            length_position = f"{row['length_position']:5.2f}" if not pd.isna(row['length_position']) else "  N/A"
            
            print(f"{row['rank']:2d}. {row['name']:<25} Overall: {overall_position} ({row['overall_tournaments']:3d}) " + 
                  f"Pattern: {pattern_position} ({row['pattern_tournaments']:2d}) " +
                  f"Length: {length_position} ({row['length_tournaments']:2d}) " +
                  f"Center: {center_position} ({row['center_tournaments']:2d}) " +
                  f"Score: {row['total_score']:5.2f}")
        
        return result
        
    def visualize_pattern_performance(self, bowler_name):
        """
        Create a visualization of a bowler's performance across different patterns
        """
        pattern_stats = self.get_pattern_performance(bowler_name)
        
        if pattern_stats.empty:
            print(f"No pattern data available for {bowler_name}")
            return None
            
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        # Create a dual-axis bar chart
        ax1 = plt.subplot(111)
        
        # Plot average position as bars (lower is better)
        bars = ax1.bar(
            pattern_stats.index, 
            pattern_stats['avg_position'],
            alpha=0.7,
            color='royalblue',
            label='Avg Position'
        )
        
        # Add tournament count as text on bars
        for bar, count in zip(bars, pattern_stats['tournaments_played']):
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.3,
                f'n={int(count)}',
                ha='center', 
                va='bottom',
                fontsize=9
            )
        
        # Invert y-axis for position (lower is better)
        ax1.set_ylim(ax1.get_ylim()[1], ax1.get_ylim()[0])
        
        # Create second y-axis for win percentage
        ax2 = ax1.twinx()
        ax2.plot(
            pattern_stats.index,
            pattern_stats['win_percentage'],
            marker='o',
            color='firebrick',
            linewidth=2,
            label='Win %'
        )
        
        # Set labels and title
        ax1.set_xlabel('Pattern Category')
        ax1.set_ylabel('Average Position (lower is better)')
        ax2.set_ylabel('Win Percentage (%)')
        plt.title(f"{bowler_name}'s Performance by Pattern Category")
        
        # Add legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center')
        
        # Add grid for readability
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        return plt
    
    def get_pattern_performance(self, bowler_name, min_tournaments=1):
        """
        Analyze a bowler's performance on different pattern categories
        """
        bowler_df = self.df[self.df['name'] == bowler_name]
    
        if len(bowler_df) == 0:
            print(f"No data found for bowler: {bowler_name}")
            return pd.DataFrame()
    
        # Check if pattern_category exists, if not try to create it
        if 'pattern_category' not in bowler_df.columns and 'pattern_length' in bowler_df.columns:
            bowler_df['pattern_category'] = pd.cut(
                bowler_df['pattern_length'],
                bins=[0, 36, 41, 47, 100],
                labels=['Short', 'Medium', 'Long', 'Extra Long']
            )
    
        # If we still don't have pattern_category, return empty DataFrame
        if 'pattern_category' not in bowler_df.columns:
            print(f"No pattern category information for bowler: {bowler_name}")
            return pd.DataFrame()
    
        # Check for missing pattern categories
        if bowler_df['pattern_category'].isna().all():
            print(f"All pattern categories are NaN for bowler: {bowler_name}")
            return pd.DataFrame()
    
        # Group by pattern category with observed=True to handle categorical data properly
        try:
            pattern_stats = bowler_df.groupby('pattern_category', observed=True).agg({
                'tournament_name': 'count',
                'position': ['mean', 'min', 'median'],
                'earnings': ['sum', 'mean'],
                'average': 'mean',
                'pattern_length': 'mean'
            })
        
            # Rename columns
            pattern_stats.columns = [
                'tournaments_played',
                'avg_position',
                'best_position',
                'median_position',
                'total_earnings',
                'avg_earnings',
                'avg_game_score',
                'avg_pattern_length'
            ]
        
            # Calculate top 5 finishes by pattern
            top5_by_pattern = bowler_df[bowler_df['position'] <= 5].groupby('pattern_category', observed=True).size()
            pattern_stats = pattern_stats.join(top5_by_pattern.rename('top5_finishes'), how='left')
            pattern_stats['top5_percentage'] = (pattern_stats['top5_finishes'] / pattern_stats['tournaments_played'] * 100).fillna(0)
        
            # Calculate wins by pattern
            wins_by_pattern = bowler_df[bowler_df['position'] == 1].groupby('pattern_category', observed=True).size()
            pattern_stats = pattern_stats.join(wins_by_pattern.rename('wins'), how='left')
            pattern_stats['win_percentage'] = (pattern_stats['wins'] / pattern_stats['tournaments_played'] * 100).fillna(0)
        
            # Fill NaN values with 0
            pattern_stats = pattern_stats.fillna(0)
        
            # Filter by minimum tournaments if needed
            if min_tournaments > 0:
                pattern_stats = pattern_stats[pattern_stats['tournaments_played'] >= min_tournaments]
        
            return pattern_stats
        except Exception as e:
            print(f"Error in get_pattern_performance for {bowler_name}: {str(e)}")
            # Return empty DataFrame
            return pd.DataFrame()

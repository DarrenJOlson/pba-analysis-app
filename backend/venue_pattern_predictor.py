import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class VenuePatternPredictor:
    def __init__(self, data_path):
        """
        Initialize the predictor with tournament data
        
        Args:
            data_path: Path to the CSV file with tournament data
        """
        print(f"Loading data for prediction from {data_path}...")
        self.df = pd.read_csv(data_path)
        self.model = None
        self._preprocess_data()
        
    def _preprocess_data(self):
        """Preprocess data for prediction"""
        # Convert dates to datetime
        for date_col in ['start_date', 'end_date']:
            if date_col in self.df.columns:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
        
        # Convert position to numeric
        if 'position' in self.df.columns:
            self.df['position_numeric'] = pd.to_numeric(self.df['position'], errors='coerce')
        
        # Convert earnings to numeric
        if 'earnings' in self.df.columns:
            self.df['earnings'] = pd.to_numeric(self.df['earnings'], errors='coerce')
        
        # Convert pattern length to numeric
        if 'pattern_length' in self.df.columns:
            self.df['pattern_length'] = pd.to_numeric(self.df['pattern_length'], errors='coerce')
            
        # Create pattern categories based on length if they don't exist
        if 'pattern_category' not in self.df.columns and 'pattern_length' in self.df.columns:
            self.df['pattern_category'] = pd.cut(
                self.df['pattern_length'],
                bins=[0, 36, 41, 47, 100],
                labels=['Short', 'Medium', 'Long', 'Extra Long']
            )
    
    def train_model(self):
        """Train the prediction model (simplified version)"""
        # In a real implementation, we might use scikit-learn or a more complex model
        # For this implementation, we'll use a simple statistical approach
        print("Training venue-pattern prediction model...")
        
        # No actual training needed for our simple approach
        self.model = True
        print("Model training complete.")
        
    def rank_bowlers_for_tournament(self, center_name, pattern_category):
        """
        Rank bowlers for a specific center and pattern combination
        With support for partial selections (center only, pattern only, or both)
        
        Args:
            center_name: Name of the bowling center or "All Centers"
            pattern_category: Category of the pattern or "All Patterns"
            
        Returns:
            DataFrame with bowler rankings
        """
        print(f"Ranking bowlers for {center_name} on {pattern_category} pattern...")
        
        # Determine filter criteria
        filter_by_center = center_name != "All Centers"
        filter_by_pattern = pattern_category != "All Patterns"
        
        # Apply data filtering based on selection
        if filter_by_center:
            # If we have prefixes like "Event: " in the center name, remove them
            if "Event: " in center_name:
                actual_center_name = center_name.replace("Event: ", "")
            elif "Location: " in center_name:
                actual_center_name = center_name.replace("Location: ", "")
            elif "Venue: " in center_name:
                actual_center_name = center_name.replace("Venue: ", "")
            else:
                actual_center_name = center_name
                
            # Try to find this center in the data
            # First check center_location since that's what we're now using
            if 'center_location' in self.df.columns:
                center_data = self.df[self.df['center_location'].str.contains(actual_center_name, case=False, na=False)]
                if len(center_data) == 0:
                    print(f"Warning: No matches found in center_location for '{actual_center_name}'. Trying other columns.")
            else:
                center_data = pd.DataFrame()
                
            # If center_location didn't work, try center_name
            if len(center_data) == 0 and 'center_name' in self.df.columns:
                center_data = self.df[self.df['center_name'].str.contains(actual_center_name, case=False, na=False)]
                
            # If center_name didn't work, try tournament_name
            if len(center_data) == 0 and 'tournament_name' in self.df.columns:
                center_data = self.df[self.df['tournament_name'].str.contains(actual_center_name, case=False, na=False)]
            
            # If we still have no matches, use all data
            if len(center_data) == 0:
                center_data = self.df
                print(f"Warning: Center '{center_name}' not found in data. Using all available data.")
        else:
            # Use all data if not filtering by center
            center_data = self.df
        
        # Get center experience for each bowler
        if filter_by_center and len(center_data) > 0:
            center_experience = center_data.groupby('name').size().reset_index(name='center_experience')
        else:
            # Create empty DataFrame with same structure
            center_experience = pd.DataFrame({'name': [], 'center_experience': []})
        
        # Filter by pattern category if needed
        if filter_by_pattern:
            if 'pattern_category' in self.df.columns:
                pattern_data = self.df[self.df['pattern_category'] == pattern_category]
                if len(pattern_data) == 0:
                    print(f"Warning: Pattern category '{pattern_category}' not found in data. Using all available data.")
                    pattern_data = self.df
            else:
                pattern_data = self.df
                print(f"Warning: Pattern category information not available. Using all available data.")
        else:
            # Use all data if not filtering by pattern
            pattern_data = self.df
        
        # Get pattern performance for each bowler
        if 'position_numeric' in pattern_data.columns:
            pattern_performance = pattern_data.groupby('name').agg({
                'position_numeric': ['mean', 'count']
            })
            pattern_performance.columns = ['avg_position_on_pattern', 'pattern_experience']
            pattern_performance = pattern_performance.reset_index()
        else:
            # Create empty DataFrame with same structure
            pattern_performance = pd.DataFrame({
                'name': [], 
                'avg_position_on_pattern': [], 
                'pattern_experience': []
            })
        
        # Get overall performance stats for all bowlers
        if 'position_numeric' in self.df.columns:
            overall_performance = self.df.groupby('name').agg({
                'position_numeric': ['mean', 'count']
            })
            overall_performance.columns = ['avg_position_overall', 'total_tournaments']
            overall_performance = overall_performance.reset_index()
        else:
            overall_performance = pd.DataFrame({
                'name': [], 
                'avg_position_overall': [], 
                'total_tournaments': []
            })
            
        # Check if we have enough data
        if len(overall_performance) == 0:
            print("Warning: No performance data available. Using sample data for demonstration.")
            # Generate sample data for demonstration
            sample_bowlers = [
                "Walter Ray Williams Jr.", "Pete Weber", "Norm Duke", "Parker Bohn III",
                "Jason Belmonte", "Chris Barnes", "Tommy Jones", "Sean Rash",
                "Bill O'Neill", "Wes Malott", "Anthony Simonsen", "EJ Tackett"
            ]
            overall_performance = pd.DataFrame({
                'name': sample_bowlers,
                'avg_position_overall': np.random.uniform(5, 25, len(sample_bowlers)),
                'total_tournaments': np.random.randint(10, 50, len(sample_bowlers))
            })
            
            pattern_performance = pd.DataFrame({
                'name': sample_bowlers,
                'avg_position_on_pattern': np.random.uniform(4, 20, len(sample_bowlers)),
                'pattern_experience': np.random.randint(1, 15, len(sample_bowlers))
            })
            
            center_experience = pd.DataFrame({
                'name': sample_bowlers,
                'center_experience': np.random.randint(0, 8, len(sample_bowlers))
            })
        
        # Combine all factors
        predictions = pd.merge(overall_performance, pattern_performance, on='name', how='left')
        predictions = pd.merge(predictions, center_experience, on='name', how='left')
        
        # Fill missing values
        predictions['pattern_experience'] = predictions['pattern_experience'].fillna(0)
        predictions['center_experience'] = predictions['center_experience'].fillna(0)
        predictions['avg_position_on_pattern'] = predictions['avg_position_on_pattern'].fillna(predictions['avg_position_overall'])
        
        # Calculate weights based on available data
        pattern_weight = 0.5 if filter_by_pattern else 0.3
        center_weight = 0.3 if filter_by_center else 0.1
        overall_weight = 1.0 - pattern_weight - center_weight
        
        # Calculate a predicted position based on weighted factors
        predictions['predicted_position'] = (
            pattern_weight * predictions['avg_position_on_pattern'] +
            center_weight * (predictions['avg_position_overall'] * (1 - 0.05 * predictions['center_experience'].clip(0, 10))) +
            overall_weight * predictions['avg_position_overall']
        )
        
        # Only include bowlers with sufficient experience
        min_tournaments = 3
        if len(predictions) > 20:  # Only filter if we have enough data
            predictions = predictions[predictions['total_tournaments'] >= min_tournaments]
        
        # Sort by predicted position (lower is better)
        predictions = predictions.sort_values('predicted_position')
        
        # Rename for readability
        predictions = predictions.rename(columns={
            'name': 'bowler',
            'avg_position_overall': 'overall_avg_position'
        })
        
        # Select relevant columns
        result_columns = [
            'bowler', 'predicted_position', 'pattern_experience', 
            'center_experience', 'overall_avg_position', 'total_tournaments'
        ]
        
        return predictions[result_columns]
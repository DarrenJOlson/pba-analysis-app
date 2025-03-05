import pandas as pd
import re
import os

def clean_pba_data(input_file, output_file=None):
    """
    Comprehensive data cleaning for PBA tournament data
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file (if None, will use input_file)
    
    Returns:
        Cleaned DataFrame
    """
    print(f"Cleaning data from {input_file}...")
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found!")
        return None
    
    # Load the data
    df = pd.read_csv(input_file)
    original_rows = len(df)
    print(f"Loaded {original_rows} rows")
    
    # 1. Fix center names - separate tournament venues from tournament names
    if 'center_name' in df.columns and 'tournament_name' in df.columns:
        print("Fixing center names...")
        # Count current unique values
        orig_centers = df['center_name'].nunique()
        
        # Create a location lookup dictionary (tournament_name -> center_name)
        location_mapping = {}
        
        # Look for center indicators in the data
        center_keywords = ['lanes', 'bowl', 'alley', 'center', 'plaza']
        
        # First pass - extract clear bowling centers
        for center in df['center_name'].dropna().unique():
            # Check if this looks like an actual bowling center
            is_center = any(keyword in center.lower() for keyword in center_keywords)
            
            if is_center:
                # Find tournaments at this center
                tournaments = df[df['center_name'] == center]['tournament_name'].unique()
                for tournament in tournaments:
                    location_mapping[tournament] = center
        
        # Second pass - extract from tournament names that contain location info
        for tournament in df['tournament_name'].dropna().unique():
            # Skip if already mapped
            if tournament in location_mapping:
                continue
                
            # Look for "at" or "in" followed by a location
            at_match = re.search(r'\bat\s+([^,]+)', tournament)
            in_match = re.search(r'\bin\s+([^,]+)', tournament)
            
            if at_match:
                location = at_match.group(1).strip()
                location_mapping[tournament] = location
            elif in_match:
                location = in_match.group(1).strip()
                location_mapping[tournament] = location
                
        # Apply the mapping where center_name is missing or same as tournament name
        for tournament, location in location_mapping.items():
            mask = (df['tournament_name'] == tournament) & (
                df['center_name'].isna() | 
                (df['center_name'] == tournament)
            )
            if mask.any():
                df.loc[mask, 'center_name'] = location
                
        # For remaining rows, if center_name == tournament_name, make it "Unknown"
        mask = df['center_name'] == df['tournament_name']
        df.loc[mask, 'center_name'] = 'Unknown Venue'
        
        # Report changes
        new_centers = df['center_name'].nunique()
        print(f"Center names: {orig_centers} unique values -> {new_centers} unique values")
    
    # 2. Fix duplicate bowler names (common misspellings)
    if 'name' in df.columns:
        print("Fixing bowler names...")
        orig_bowlers = df['name'].nunique()
        
        # Common name variations and corrections
        name_corrections = {
            # Format: 'incorrect': 'correct'
            'Zac Tackett': 'Zac Tackett',
            'Zachary Tackett': 'Zac Tackett',
            'Tom Daugherty': 'Tom Daugherty',
            'Tom Daughterty': 'Tom Daugherty',
            # Add more name corrections as needed
        }
        
        # Apply name corrections
        df['name'] = df['name'].replace(name_corrections)
        
        # Fix capitalization variations (e.g., "john smith" -> "John Smith")
        df['name'] = df['name'].str.title()
        
        # Remove extra spaces
        df['name'] = df['name'].str.strip()
        df['name'] = df['name'].replace(r'\s+', ' ', regex=True)
        
        # Report changes
        new_bowlers = df['name'].nunique()
        print(f"Bowler names: {orig_bowlers} unique values -> {new_bowlers} unique values")
    
    # 3. Standardize pattern names and lengths
    if 'pattern_name' in df.columns and 'pattern_length' in df.columns:
        print("Standardizing oil patterns...")
        orig_patterns = df['pattern_name'].nunique()
        
        # Known pattern names and their standard lengths
        pattern_standards = {
            'cheetah': 35,
            'wolf': 33,
            'chameleon': 41,
            'scorpion': 42,
            'shark': 48,
            'bear': 40,
            'dragon': 45,
            'viper': 39,
            'us open': 45,
            'masters': 40,
            'toc': 43,
            'tournament of champions': 43,
            'mike aulby': 39,
            'amleto monacelli': 40,
            'billy hardwick': 44,
            'don johnson': 40,  # Specifically fixing Don Johnson pattern
            'earl anthony': 43,
            'don carter': 37,
            'wayne webb': 38,
            'carmen salvino': 42,
            'dick weber': 45
        }
        
        # Pattern name normalization (lowercase and trim)
        df['pattern_name_lower'] = df['pattern_name'].str.lower().str.strip()
        
        # Apply standard lengths for known patterns
        for pattern, length in pattern_standards.items():
            # Exact match on lowercase name
            mask = df['pattern_name_lower'] == pattern
            df.loc[mask, 'pattern_length'] = length
            
            # Contains pattern name (for variations like "Don Johnson 40")
            contains_mask = df['pattern_name_lower'].str.contains(fr'\b{re.escape(pattern)}\b', regex=True, na=False)
            df.loc[contains_mask, 'pattern_length'] = length
        
        # Remove temporary column
        df = df.drop(columns=['pattern_name_lower'])
        
        # Add pattern category based on length
        # Short: 0-36, Medium: 37-41, Long: 42-47, Extra Long: 48+
        df['pattern_category'] = pd.cut(
            df['pattern_length'],
            bins=[0, 36, 41, 47, 100],
            labels=['Short', 'Medium', 'Long', 'Extra Long']
        )
        
        # Report changes
        new_patterns = df['pattern_name'].nunique()
        print(f"Patterns: {orig_patterns} unique values -> {new_patterns} unique values")
    
    # 4. Add a flag for tournament type (PTQ vs. main tournament)
    print("Adding tournament classification...")
    if 'tournament_name' in df.columns:
        # Identify PTQ events vs main tournaments
        df['is_ptq'] = df['tournament_name'].str.lower().str.contains('ptq|qualifier|qualifying', na=False)
        
        # Add a field for tournament tier
        conditions = [
            # Major tournaments
            df['tournament_name'].str.lower().str.contains('major|masters|us open|pba world|tournament of champions|players championship', na=False),
            # Standard tournaments
            ~df['is_ptq'] & ~df['tournament_name'].str.lower().str.contains('regional|challenge|trial', na=False),
            # PTQ/Qualifiers
            df['is_ptq'],
            # Regionals/Challenges
            df['tournament_name'].str.lower().str.contains('regional|challenge', na=False)
        ]
        
        choices = ['Major', 'Standard', 'Qualifier', 'Regional']
        df['tournament_tier'] = np.select(conditions, choices, default='Other')
        
        # Print distribution
        tier_counts = df['tournament_tier'].value_counts()
        print("Tournament tiers distribution:")
        for tier, count in tier_counts.items():
            print(f"  {tier}: {count} entries")
    
    # 5. Final cleanup - convert data types, handle missing values
    print("Final data cleanup...")
    
    # Convert position to numeric (handling 'T' prefix for ties)
    if 'position' in df.columns:
        df['position'] = df['position'].astype(str).str.replace('T', '', regex=False)
        df['position'] = pd.to_numeric(df['position'], errors='coerce')
    
    # Convert earnings to numeric
    if 'earnings' in df.columns:
        df['earnings'] = df['earnings'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
        df['earnings'] = pd.to_numeric(df['earnings'], errors='coerce')
    
    # Convert dates to datetime
    for date_col in ['start_date', 'end_date']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Handle missing values
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if col != 'position':  # Don't fill position
            df[col] = df[col].fillna(0)
    
    # Save cleaned data
    if output_file is None:
        output_file = input_file
        
    df.to_csv(output_file, index=False)
    print(f"Saved cleaned data to {output_file}")
    
    return df

# For testing
if __name__ == "__main__":
    import numpy as np
    import sys
    
    # Use command line argument or default
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/combined_pba_data.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/combined_pba_data_cleaned.csv"
    
    clean_pba_data(input_file, output_file)

import pandas as pd
import os

def update_pattern_lengths(input_csv="data/combined_pba_data.csv", output_csv="data/combined_pba_data_updated.csv"):
    """
    Updates the CSV file with missing pattern lengths based on pattern names.
    """
    print(f"Loading CSV file: {input_csv}")
    if not os.path.exists(input_csv):
        print(f"Error: File {input_csv} not found!")
        return
    
    # Load the CSV file
    df = pd.read_csv(input_csv)
    original_missing = df['pattern_length'].isna().sum()
    print(f"Original file has {original_missing} rows with missing pattern lengths")
    
    # Define pattern lengths dictionary
    pattern_lengths = {
        'cheetah': 35,
        'wolf': 33,
        'bat': 37,
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
        'don johnson': 40,
        'mark roth': 43,
        'marshall holman': 38,
        'earl anthony': 43,
        'don carter': 37,
        'wayne webb': 38,
        'carmen salvino': 42,
        'dick weber': 45
    }
    
    # Create a category column if it doesn't exist
    if 'pattern_category' not in df.columns:
        df['pattern_category'] = None
    
    # Track updates for reporting
    update_counts = {}
    total_updates = 0
    
    # Update pattern lengths where missing
    for pattern_name, length in pattern_lengths.items():
        # Convert pattern name in DataFrame to lowercase for case-insensitive comparison
        mask = df['pattern_name'].str.lower().str.contains(pattern_name.lower(), na=False)
        # Only update where length is missing
        mask = mask & df['pattern_length'].isna()
        
        # Count how many rows will be updated for this pattern
        update_count = mask.sum()
        if update_count > 0:
            update_counts[pattern_name] = update_count
            total_updates += update_count
            
            # Update the length
            df.loc[mask, 'pattern_length'] = length
            
            # Update pattern category based on length
            # Short: 0-36, Medium: 37-41, Long: 42-47, Extra Long: 48+
            category = None
            if length <= 36:
                category = 'Short'
            elif length <= 41:
                category = 'Medium'
            elif length <= 47:
                category = 'Long'
            else:
                category = 'Extra Long'
                
            df.loc[mask, 'pattern_category'] = category
    
    # Report on updates made
    print(f"\nUpdated {total_updates} rows with missing pattern lengths:")
    for pattern, count in update_counts.items():
        print(f"  {pattern}: {count} rows updated to length {pattern_lengths[pattern]}")
    
    # Check if any missing pattern lengths remain
    remaining_missing = df['pattern_length'].isna().sum()
    print(f"\nRemaining rows with missing pattern lengths: {remaining_missing}")
    
    # Save the updated CSV
    df.to_csv(output_csv, index=False)
    print(f"\nSaved updated data to {output_csv}")
    
    # Return success/failure
    return total_updates > 0

if __name__ == "__main__":
    # You can pass custom file paths as arguments
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/combined_pba_data.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/combined_pba_data_updated.csv"
    
    update_pattern_lengths(input_file, output_file)

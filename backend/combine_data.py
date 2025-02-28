import pandas as pd
import os
import glob

def combine_csv_files(directory="data", output_file="data/combined_pba_data.csv"):
    """
    Combines all PBA results CSV files in the specified directory
    """
    print("Combining PBA data files...")
    
    # Get all CSV files matching the pattern pba_results_YYYY.csv
    csv_files = glob.glob(os.path.join(directory, "pba_results_*.csv"))
    
    if not csv_files:
        print(f"No PBA results CSV files found in {directory}")
        return None
    
    print(f"Found {len(csv_files)} CSV files: {csv_files}")
    
    # Read and combine all CSV files
    combined_df = pd.concat([pd.read_csv(file) for file in csv_files], ignore_index=True)
    
    # Clean up the data
    # Convert match play record back to normal format if it has quotes
    if 'match_play_record' in combined_df.columns:
        combined_df['match_play_record'] = combined_df['match_play_record'].str.replace("'", "")
    
    # Convert position to numeric
    if 'position' in combined_df.columns:
        combined_df['position'] = pd.to_numeric(combined_df['position'], errors='coerce')
    
    # Convert earnings to numeric
    if 'earnings' in combined_df.columns:
        combined_df['earnings'] = pd.to_numeric(combined_df['earnings'], errors='coerce')
    
    # Convert dates to datetime
    for date_col in ['start_date', 'end_date']:
        if date_col in combined_df.columns:
            combined_df[date_col] = pd.to_datetime(combined_df[date_col], errors='coerce')
    
    # Save the combined data
    combined_df.to_csv(output_file, index=False)
    print(f"Saved combined data to {output_file} with {len(combined_df)} total results")
    
    return combined_df

if __name__ == "__main__":
    # Combine all CSV files
    combined_data = combine_csv_files()
    
    if combined_data is not None:
        # Print some summary stats
        print("\nSummary statistics:")
        print(f"Total tournaments: {combined_data['tournament_name'].nunique()}")
        print(f"Total unique bowlers: {combined_data['name'].nunique()}")
        print(f"Date range: {combined_data['start_date'].min()} to {combined_data['start_date'].max()}")
        
        # Count by pattern
        pattern_counts = combined_data.groupby('pattern_name').size().reset_index(name='count')
        pattern_counts = pattern_counts.sort_values('count', ascending=False)
        
        print("\nMost common patterns:")
        for _, row in pattern_counts.head(10).iterrows():
            print(f"{row['pattern_name']}: {row['count']} results")

import os
import pandas as pd
import matplotlib.pyplot as plt
from pattern_analyzer import PBAAnalyzer
from combine_data import combine_csv_files

def run_tournament_analysis(pattern_name=None, pattern_length=None, center_name=None):
    """
    Run a complete analysis pipeline for an upcoming tournament
    """
    # Step 1: Ensure we have combined data
    combined_data_path = "data/combined_pba_data.csv"
    if not os.path.exists(combined_data_path):
        print("Combined data file not found. Creating it now...")
        combine_csv_files()
    
    # Step 2: Initialize the analyzer
    analyzer = PBAAnalyzer(combined_data_path)
    
    # Step 3: Get tournament predictions using multi-factor approach
    predictions = analyzer.get_multi_factor_prediction(
        pattern_name=pattern_name,
        pattern_length=pattern_length,
        center_name=center_name,
        recency_months=None,  # Use ALL data, not just recent data
        min_events_overall=3,
        top_n=15
    )
    
    if predictions is None or predictions.empty:
        print("Not enough data to make predictions")
        return
        
    # Step 4: Analyze the top predicted bowlers in more detail
    print("\n===== TOP BOWLER DETAILED ANALYSIS =====")
    top_bowlers = predictions['name'].head(5).tolist()
    
    for bowler in top_bowlers:
        print(f"\nDetailed analysis for {bowler}:")
        
        # Performance by pattern category
        pattern_category_stats = analyzer.get_pattern_performance(bowler)
        if not pattern_category_stats.empty:
            print("Performance by pattern category:")
            for category, row in pattern_category_stats.iterrows():
                print(f"  {category}: Avg Pos {row['avg_position']:.2f} in {int(row['tournaments_played'])} events")
        
        # Create visualization if enough data
        if not pattern_category_stats.empty and len(pattern_category_stats) >= 2:
            plt.figure(figsize=(10, 6))
            analyzer.visualize_pattern_performance(bowler)
            plt.tight_layout()
            
            # Save the plot
            os.makedirs("analysis_results", exist_ok=True)
            plt.savefig(f"analysis_results/{bowler.replace(' ', '_')}_pattern_analysis.png")
            plt.close()
        
    # Step 5: Save predictions to CSV
    os.makedirs("analysis_results", exist_ok=True)
    pattern_desc = pattern_name if pattern_name else f"{pattern_length}ft"
    pattern_desc = pattern_desc.replace(" ", "_") if pattern_desc else "unknown"
    center_desc = f"_{center_name.replace(' ', '_')}" if center_name else ""
    predictions_file = f"analysis_results/predictions_{pattern_desc}{center_desc}.csv"
    predictions.to_csv(predictions_file, index=False)
    print(f"\nSaved predictions to {predictions_file}")
    
    print("\nAnalysis complete! Check the 'analysis_results' folder for visualization and CSV files.")
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze PBA tournament data and make predictions")
    parser.add_argument("--pattern", help="Pattern name (e.g., 'Cheetah', 'Weber')")
    parser.add_argument("--length", type=int, help="Pattern length in feet (e.g., 39, 42)")
    parser.add_argument("--center", help="Bowling center name")
    
    args = parser.parse_args()
    
    # If no arguments provided, show interactive input
    if not (args.pattern or args.length):
        print("No pattern specified. Please provide pattern information:")
        pattern_input = input("Pattern name (leave blank if unknown): ").strip()
        pattern_name = pattern_input if pattern_input else None
        
        if not pattern_name:
            length_input = input("Pattern length in feet (e.g., 39, 42): ").strip()
            pattern_length = int(length_input) if length_input and length_input.isdigit() else None
        else:
            pattern_length = None
        
        center_name = input("Bowling center name (optional): ").strip()
        center_name = center_name if center_name else None
    else:
        pattern_name = args.pattern
        pattern_length = args.length
        center_name = args.center
    
    # Run the analysis
    run_tournament_analysis(
        pattern_name=pattern_name,
        pattern_length=pattern_length,
        center_name=center_name
    )

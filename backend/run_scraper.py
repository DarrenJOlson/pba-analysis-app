from pba_scraper import PBAScraper
import os
import sys

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)
os.makedirs('data/results', exist_ok=True)

# Initialize scraper
scraper = PBAScraper()

# Use command line argument for year, or default to 2023
year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
print(f"Scraping PBA tournament data for {year}...")

# Run the scraper
results = scraper.scrape_year(year)

# Save results
if results:
    json_file = f"data/results/pba_results_{year}.json"
    csv_file = f"data/pba_results_{year}.csv"

    print(f"Saving results to {json_file} and {csv_file}...")
    scraper.save_results(results, json_file)
    scraper.save_to_csv(results, csv_file)

    print(f"Successfully scraped {len(results)} tournaments with {sum(len(t.get('results', [])) for t in results)} bowler results.")
else:
    print("No tournament results were found.")

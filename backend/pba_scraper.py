import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from datetime import datetime
import pandas as pd

class PBAScraper:
    def __init__(self):
        self.base_url = "https://www.pba.com"
        self.archive_url = f"{self.base_url}/tournament-archive"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Known oil pattern lengths for common pattern names
        self.known_patterns = {
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
            'don johnson': 40,
            'earl anthony': 43,
            'don carter': 37,
            'wayne webb': 38,
            'carmen salvino': 42,
            'dick weber': 45
        }
        
    def get_tournament_list(self, year, type_id=None):
        """
        Fetches list of tournaments for a given year
        If type_id is None, tries a few specific types
        """
        # Try specific type IDs that are likely to be PBA events
        if type_id is None:
            type_ids = [61, 60, 58]  # Main PBA tour events, likely type IDs
            tournaments = []
            
            for tid in type_ids:
                print(f"Trying to get tournaments with type_id={tid}")
                url = f"{self.archive_url}?type={tid}&year={year}"
                    
                result = self._get_tournaments_from_url(url, year)
                if result:
                    tournaments.extend(result)
                    print(f"Found {len(result)} tournaments with type_id={tid}")
            
            # Remove duplicates based on URL
            unique_tournaments = []
            seen_urls = set()
            for t in tournaments:
                if t['url'] not in seen_urls:
                    unique_tournaments.append(t)
                    seen_urls.add(t['url'])
            
            return unique_tournaments
        else:
            # Use the specified type ID
            url = f"{self.archive_url}?type={type_id}&year={year}"
            return self._get_tournaments_from_url(url, year)
    
    def _get_tournaments_from_url(self, url, year):
        """
        Helper method to extract tournaments from a specific URL
        """
        print(f"Accessing URL: {url}")
        
        response = requests.get(url, headers=self.headers)
        print(f"Response status: {response.status_code}")
        
        # Create debug directory if it doesn't exist
        os.makedirs("debug", exist_ok=True)
        
        # Extract URL identifier for debug file
        url_id = url.split('?')[-1].replace('=', '_').replace('&', '_')
        
        # Save HTML for debugging
        with open(f"debug/pba_archive_{url_id}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tournaments = []
        
        # Try to find the tournament table - multiple methods
        # 1. Look for tables with specific classes
        table = None
        for table_class in ['cols-5', 'views-table', 'tournaments-table', 'table']:
            tables = soup.find_all('table', class_=table_class)
            if tables:
                print(f"Found {len(tables)} tables with class '{table_class}'")
                table = tables[0]  # Use the first matching table
                break
                
        # 2. If no table found with known classes, try any table with enough rows
        if not table:
            print("Trying tables without specific class...")
            all_tables = soup.find_all('table')
            print(f"Found {len(all_tables)} tables on the page")
            
            for i, t in enumerate(all_tables):
                rows = t.find_all('tr')
                if len(rows) > 3:  # Needs header + some data rows
                    print(f"Using table #{i} with {len(rows)} rows")
                    table = t
                    break
        
        if not table:
            print("No suitable tables found")
            return tournaments
            
        # Process tournament rows
        rows = table.find_all('tr')[1:]  # Skip header row
        print(f"Processing {len(rows)} table rows")
        
        for row_index, row in enumerate(rows):
            try:
                print(f"\nExamining row {row_index+1}")
                # Extract data from columns
                cols = row.find_all('td')
                if len(cols) < 2:  # Need at least two columns
                    print("Not enough columns, skipping")
                    continue
                
                # Print all column texts
                for i, col in enumerate(cols):
                    print(f"Col {i}: {col.text.strip()}")
                
                # Extract info from columns
                tournament_name = None
                tournament_link = None
                date_text = None
                location = None
                
                # Step 1: Find tournament name (usually column 1 with the longest text)
                # Look for the column that most likely contains the tournament name
                # (Typically not the first column, which is usually dates)
                name_col_candidates = []
                for i, col in enumerate(cols):
                    if i == 0:  # Skip first column (usually dates)
                        continue
                        
                    text = col.text.strip()
                    # Skip very short text or "More Info" text
                    if len(text) < 5 or text.lower() == "more info":
                        continue
                        
                    # Skip columns that look like locations (contain commas or state codes)
                    if ',' in text or re.search(r'\b[A-Z]{2}\b', text):
                        location = text  # Save as location
                        continue
                        
                    # Add as a candidate for tournament name
                    name_col_candidates.append((i, text))
                
                # Use the longest text as the tournament name
                if name_col_candidates:
                    name_col_candidates.sort(key=lambda x: len(x[1]), reverse=True)
                    tournament_name = name_col_candidates[0][1]
                    print(f"Found tournament name: {tournament_name}")
                
                # Step 2: Find the link (usually in the "More Info" column)
                for i, col in enumerate(cols):
                    links = col.find_all('a')
                    if links:
                        for link in links:
                            href = link.get('href')
                            if href:
                                if href.startswith('/'):
                                    tournament_link = f"{self.base_url}{href}"
                                else:
                                    tournament_link = href
                                print(f"Found tournament link: {tournament_link}")
                                break
                    if tournament_link:
                        break
                
                # Step 3: Extract dates from first column
                if len(cols) > 0:
                    date_text = cols[0].text.strip()
                    # Extract dates from text
                    dates = []
                    time_elements = cols[0].find_all('time')
                    if time_elements:
                        for time_elem in time_elements:
                            if 'datetime' in time_elem.attrs:
                                dates.append(time_elem['datetime'])
                
                # If we've failed to find a tournament name, skip this row
                if not tournament_name:
                    print("No valid tournament name found, skipping")
                    continue
                
                # If we've failed to find a tournament link, construct one from the name
                if not tournament_link:
                    tournament_link = f"{self.base_url}/tournaments/{year}/{self.create_url_slug(tournament_name)}"
                    print(f"Constructed URL: {tournament_link}")
                
                # Extract dates
                start_date = None
                end_date = None
                
                # Look for time elements with datetime attribute
                for col in cols:
                    time_elements = col.find_all('time')
                    if time_elements and len(time_elements) > 0:
                        if 'datetime' in time_elements[0].attrs:
                            start_date = time_elements[0]['datetime']
                        if len(time_elements) > 1 and 'datetime' in time_elements[1].attrs:
                            end_date = time_elements[1]['datetime']
                        break
                
                # If we haven't found a location yet, look for it
                if not location:
                    for i, col in enumerate(cols):
                        text = col.text.strip()
                        # Locations often have commas or state abbreviations
                        if ',' in text or re.search(r'\b[A-Z]{2}\b', text):
                            # Exclude column if it contains the tournament name (to avoid confusion)
                            if tournament_name not in text:
                                location = text
                                break
                
                # Create tournament object
                tournament = {
                    'name': tournament_name,
                    'location': location or "",
                    'start_date': start_date,
                    'end_date': end_date,
                    'year': year,
                    'url': tournament_link
                }
                
                print(f"Adding tournament: {tournament['name']}")
                tournaments.append(tournament)
            except Exception as e:
                print(f"Error processing row: {str(e)}")
        
        return tournaments
        
    def create_url_slug(self, title):
        """
        Creates URL slug from tournament title
        """
        slug = title.lower()
        slug = slug.replace(" of ", "-")
        slug = re.sub(r'[^a-z0-9-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug

    def get_tournament_results(self, tournament_url):
        """
        Scrapes results from a specific tournament page
        """
        print(f"Fetching tournament details from: {tournament_url}")
        
        response = requests.get(tournament_url, headers=self.headers)
        print(f"Response status: {response.status_code}")
        
        # Skip if page not found
        if response.status_code == 404:
            print("Page not found (404), skipping...")
            return None
        
        # Extract tournament ID from URL for debug file
        tournament_id = tournament_url.split('/')[-1]
        debug_file = f"debug/tournament_{tournament_id}.html"
        
        # Save HTML for debugging
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract tournament name first for pattern extraction context
        tournament_name = self._extract_tournament_name(soup, tournament_id)
        print(f"Tournament name: {tournament_name}")
        
        # Extract pattern info with tournament name for context
        pattern_info = self.extract_pattern_info(soup, tournament_name)
        
        # Extract tournament details
        tournament_info = {
            'name': tournament_name,
            'url': tournament_url,
            'start_date': None,
            'end_date': None,
            'center': {
                'name': '',
                'location': '',
            },
            'pattern': pattern_info,
            'results': []
        }
        
        # Get dates
        tournament_info.update(self._extract_dates(soup))
        
        # Get center info
        center_info = self._extract_center_info(soup)
        tournament_info['center'] = center_info
        
        # Extract results using multiple methods
        tournament_info['results'] = self._extract_results(soup)
        print(f"Found {len(tournament_info['results'])} bowler results")
        
        # If we have few results (likely just the stepladder finals), 
        # look for a Full Standings section or link
        if len(tournament_info['results']) < 10:
            print("Few results found, looking for full standings...")
            full_standings = self._find_full_standings(soup, tournament_url)
            if full_standings and len(full_standings) > len(tournament_info['results']):
                print(f"Found {len(full_standings)} results in full standings!")
                tournament_info['results'] = full_standings
        
        return tournament_info
    
    def _find_full_standings(self, soup, tournament_url):
        """Look for full standings on the page or through a 'Full Standings' link"""
        
        # Method 1: Look for a "Full Standings" or "Complete Results" link
        for link_text in ['full standings', 'complete results', 'all results', 'view standings']:
            full_standings_link = soup.find('a', string=re.compile(link_text, re.IGNORECASE))
            if full_standings_link:
                href = full_standings_link.get('href')
                if href:
                    # Make URL absolute if it's relative
                    if href.startswith('/'):
                        href = f"{self.base_url}{href}"
                    
                    print(f"Found full standings link: {href}")
                    try:
                        # Fetch the full standings page
                        response = requests.get(href, headers=self.headers)
                        if response.status_code == 200:
                            # Save for debugging
                            with open(f"debug/full_standings_{tournament_url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
                                f.write(response.text)
                            
                            # Extract results from this page
                            full_soup = BeautifulSoup(response.text, 'html.parser')
                            return self._extract_results(full_soup)
                    except Exception as e:
                        print(f"Error fetching full standings: {str(e)}")
        
        # Method 2: Look for section with id or class containing "standings"
        standings_sections = soup.find_all(lambda tag: tag.name == 'div' and 
                                          (tag.get('id') and 'standings' in tag.get('id').lower() or
                                           tag.get('class') and 'standings' in ' '.join(tag.get('class')).lower()))
        
        for section in standings_sections:
            # Look for tables within this section
            tables = section.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 10:  # Likely a full standings table
                    print(f"Found likely full standings table with {len(rows)} rows")
                    results = self._extract_results_from_table(table)
                    if len(results) > 5:  # More than just stepladder finalists
                        return results
        
        # Method 3: Look for headers or text indicating full standings
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            if 'full standings' in heading.text.lower() or 'complete results' in heading.text.lower():
                # Look for a table following this heading
                table = heading.find_next('table')
                if table:
                    results = self._extract_results_from_table(table)
                    if len(results) > 5:
                        return results
        
        # No full standings found
        return []
    
    def _extract_tournament_name(self, soup, fallback_id):
        """Extract tournament name from the page"""
        # Try meta tags first
        meta_title = soup.find('meta', property='og:title')
        if meta_title and 'content' in meta_title.attrs:
            return meta_title['content']
        
        # Try page title
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            # Often format is "Title | PBA" or similar
            if '|' in title_text:
                return title_text.split('|')[0].strip()
            return title_text
        
        # Try main heading
        h1 = soup.find('h1')
        if h1:
            return h1.text.strip()
        
        # Try other heading levels
        for tag in ['h2', 'h3']:
            headings = soup.find_all(tag)
            for heading in headings:
                text = heading.text.strip()
                if len(text) > 15 and any(kw in text.lower() for kw in ['tournament', 'championship', 'open']):
                    return text
        
        # Return fallback from URL
        return fallback_id.replace('-', ' ').title()
    
    def _extract_dates(self, soup):
        """Extract tournament dates"""
        dates_info = {
            'start_date': None,
            'end_date': None
        }
        
        # Try time elements
        dates = soup.find_all('time', class_='datetime')
        if dates:
            if len(dates) >= 1 and 'datetime' in dates[0].attrs:
                dates_info['start_date'] = dates[0]['datetime']
            if len(dates) >= 2 and 'datetime' in dates[1].attrs:
                dates_info['end_date'] = dates[1]['datetime']
            return dates_info
        
        # Try date fields
        date_fields = soup.find_all(class_=lambda c: c and any(kw in c.lower() for kw in ['date', 'when']))
        for field in date_fields:
            text = field.text.strip()
            date_matches = re.findall(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', text)
            
            for date_match in date_matches:
                if '/' in date_match:  # Convert MM/DD/YYYY to YYYY-MM-DD
                    parts = date_match.split('/')
                    if len(parts) == 3 and len(parts[2]) == 4:  # Ensure it's MM/DD/YYYY
                        date_match = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                
                if not dates_info['start_date']:
                    dates_info['start_date'] = date_match
                elif not dates_info['end_date']:
                    dates_info['end_date'] = date_match
                    break
        
        return dates_info
    
    def _extract_center_info(self, soup):
        """Extract bowling center information"""
        center_info = {
            'name': '',
            'location': ''
        }
        
        # Try field--name-title for center name
        center_name = soup.find('span', class_='field--name-title')
        if center_name:
            center_info['name'] = center_name.text.strip()
            print(f"Center name: {center_info['name']}")
        
        # Try field--name-field-address for location
        center_address = soup.find('div', class_='field--name-field-address')
        if center_address:
            center_info['location'] = ' '.join([
                span.text.strip() 
                for span in center_address.find_all('span')
            ])
            print(f"Center location: {center_info['location']}")
        
        # If we don't have a center name yet, look for venue information
        if not center_info['name']:
            venue_keywords = ['venue', 'location', 'center', 'bowling']
            for keyword in venue_keywords:
                elements = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    parent = element.parent
                    # Look for patterns like "Venue: Center Name" or "Location: Center Address"
                    if ':' in parent.text:
                        parts = parent.text.split(':', 1)
                        if keyword.lower() in parts[0].lower():
                            value = parts[1].strip()
                            if not center_info['name'] and len(value) < 100:  # Reasonable length for name
                                center_info['name'] = value
                            elif not center_info['location'] and ',' in value:  # Location likely has commas
                                center_info['location'] = value
        
        return center_info
    
    def _extract_results(self, soup):
        """Extract tournament results using multiple methods"""
        results = []
        largest_results = []
        
        # Track the largest set of results found
        def update_largest_results(new_results):
            nonlocal largest_results
            if len(new_results) > len(largest_results):
                largest_results = new_results
        
        # Method 1: Standard tournament-standings div
        standings_div = soup.find('div', class_='tournament-standings')
        if standings_div:
            print("Found tournament-standings div")
            # Find all tables in the standings div - there might be multiple for different rounds
            tables = standings_div.find_all('table')
            for i, table in enumerate(tables):
                print(f"Examining standings table #{i+1}")
                table_results = self._extract_results_from_table(table)
                print(f"Found {len(table_results)} results in table #{i+1}")
                update_largest_results(table_results)
        
        # Method 2: Any table with result-like headers
        print("Examining all tables for results...")
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            headers = [th.text.strip().lower() for th in table.find_all('th')]
            header_text = ' '.join(headers)
            
            # Check if this looks like a results table
            if any(kw in header_text for kw in ['pos', 'player', 'name', 'score', 'earnings', 'finish', 'bowler']):
                print(f"Found potential results table #{i+1} with headers: {headers}")
                table_results = self._extract_results_from_table(table)
                print(f"Found {len(table_results)} results in table #{i+1}")
                update_largest_results(table_results)
        
        # Method 3: Look for divs with result-related classes/ids
        print("Looking for divs with result-related classes...")
        result_keywords = ['standings', 'results', 'leaderboard', 'scorecard']
        for keyword in result_keywords:
            divs = soup.find_all(lambda tag: tag.name == 'div' and 
                                 (tag.get('class') and keyword in ' '.join(tag.get('class')).lower() or
                                  tag.get('id') and keyword in tag.get('id').lower()))
            
            for div in divs:
                tables = div.find_all('table')
                for i, table in enumerate(tables):
                    table_results = self._extract_results_from_table(table)
                    print(f"Found {len(table_results)} results in {keyword} div table #{i+1}")
                    update_largest_results(table_results)
        
        # Method 4: Try to extract from structured lists
        print("Looking for results in structured lists...")
        lists = soup.find_all(['ol', 'ul'])
        for list_elem in lists:
            if len(list_elem.find_all('li')) > 5:  # Only consider lists with several items
                list_results = self._extract_results_from_list(list_elem)
                print(f"Found {len(list_results)} results in a list")
                update_largest_results(list_results)
        
        # Use the largest set of results found
        if largest_results:
            print(f"Using largest result set found with {len(largest_results)} bowlers")
            results = largest_results
        
        return results
    
    def _extract_results_from_table(self, table):
        """Extract results from a table element"""
        results = []
        
        # Get table headers if available
        headers = [th.text.strip().lower() for th in table.find_all('th')]
        
        # Get table rows (skip header row)
        rows = table.find_all('tr')[1:] if table.find_all('tr') else []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 2:  # Need at minimum position and name
                continue
                
            result = {}
            
            # If we have headers, use them to map columns
            if headers and len(headers) > 0:
                for i, header in enumerate(headers):
                    if i < len(cols):
                        # Map common header names to standardized keys
                        key = header.lower().replace(' ', '_')
                        key = self._standardize_header_key(key)
                        result[key] = cols[i].text.strip()
            else:
                # Without headers, make best guess based on column position and content
                # Position is typically the first column
                if len(cols) > 0:
                    result['position'] = cols[0].text.strip()
                
                # Name is typically the second column
                if len(cols) > 1:
                    result['name'] = cols[1].text.strip()
                
                # Handle other columns based on content patterns
                for i, col in enumerate(cols[2:], 2):
                    text = col.text.strip()
                    
                    # Try to identify column by content
                    if re.match(r'^\d+-\d+-\d+$', text):  # Looks like W-L-T record
                        result['match_play_record'] = text
                    elif re.match(r'^\d+\.\d+$', text):  # Looks like average
                        result['average'] = text
                    elif re.match(r'^[\$]?\d+,?\d*\.?\d*$', text):  # Looks like earnings
                        result['earnings'] = text.replace('$', '').replace(',', '')
            
            # Clean up position (handle tied positions with T prefix)
            if 'position' in result:
                result['position'] = result['position'].replace('T', '').strip()
            
            # Clean up earnings
            if 'earnings' in result:
                result['earnings'] = result['earnings'].replace('$', '').replace(',', '')
            
            # Add quotes to match play record to prevent CSV from interpreting as date
            if 'match_play_record' in result:
                result['match_play_record'] = f"'{result['match_play_record']}'"
            
            # Only add if we have at least position and name
            if 'position' in result and 'name' in result:
                results.append(result)
        
        return results
    
    def _extract_results_from_list(self, list_elem):
        """Extract results from an ordered or unordered list"""
        results = []
        
        items = list_elem.find_all('li')
        for item in items:
            text = item.text.strip()
            
            # Look for patterns like "1. Player Name" or "Player Name - 235"
            pos_name_match = re.search(r'^(\d+)\.?\s+([A-Za-z\s\'-]+)', text)
            if pos_name_match:
                pos = pos_name_match.group(1)
                name = pos_name_match.group(2).strip()
                
                result = {
                    'position': pos,
                    'name': name
                }
                
                # Try to extract score or earnings if available
                remaining_text = text[text.find(name) + len(name):]
                
                # Look for earnings ($ followed by numbers)
                earnings_match = re.search(r'\$\s*(\d+,?\d*\.?\d*)', remaining_text)
                if earnings_match:
                    result['earnings'] = earnings_match.group(1).replace(',', '')
                
                # Look for score (just numbers, possibly with commas)
                elif not earnings_match:
                    score_match = re.search(r'(\d+,?\d*)', remaining_text)
                    if score_match:
                        result['score'] = score_match.group(1).replace(',', '')
                
                results.append(result)
        
        return results
    
    def _standardize_header_key(self, key):
        """Convert various header names to standard keys"""
        # Map for common header variations
        header_map = {
            'pos': 'position',
            'position': 'position',
            'rank': 'position',
            'finish': 'position',
            'place': 'position',
            '#': 'position',
            
            'player': 'name',
            'bowler': 'name',
            'name': 'name',
            'athlete': 'name',
            
            'hometown': 'hometown',
            'city': 'hometown',
            'from': 'hometown',
            
            'record': 'match_play_record',
            'match_play': 'match_play_record',
            'w-l-t': 'match_play_record',
            '(w-l-t)': 'match_play_record',
            
            'avg': 'average',
            'average': 'average',
            
            'score': 'score',
            'pins': 'score',
            'pinfall': 'score',
            'total': 'score',
            
            'earnings': 'earnings',
            'prize': 'earnings',
            'money': 'earnings',
            'winnings': 'earnings',
            'won': 'earnings',
            '$': 'earnings',
            
            'points': 'points',
            'pts': 'points',
            'pts points': 'points'
        }
        
        # Check for matches in the map
        for pattern, replacement in header_map.items():
            if pattern in key:
                return replacement
        
        return key  # If no match, return original
        
    def extract_pattern_info(self, soup, tournament_name=""):
        """
        Extracts detailed oil pattern information
        """
        pattern_info = {
            'name': None,
            'length': None,
            'volume': None,
            'ratio': None
        }
        
        # Find the oil pattern section
        pattern_section = soup.find('div', id='collapse-oil-patterns')
        if pattern_section:
            print("Found oil pattern section")
            # Get pattern name
            pattern_title = pattern_section.find('span', class_='field--name-title')
            if pattern_title:
                pattern_info['name'] = pattern_title.text.strip()
                print(f"Pattern name: {pattern_info['name']}")
            
            # Look for pattern specifications
            pattern_specs = pattern_section.find_all('div', class_='field__item')
            for spec in pattern_specs:
                text = spec.text.strip().lower()
                if 'length' in text:
                    # Extract length (assuming format like "Length: 45 feet")
                    length_match = re.search(r'(\d+)\s*(?:ft|feet)', text)
                    if length_match:
                        pattern_info['length'] = int(length_match.group(1))
                        print(f"Pattern length: {pattern_info['length']} feet")
                if 'volume' in text:
                    # Extract volume if available
                    volume_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ml|milliliters?)', text)
                    if volume_match:
                        pattern_info['volume'] = float(volume_match.group(1))
                        print(f"Pattern volume: {pattern_info['volume']} ml")
                if 'ratio' in text:
                    # Extract ratio if available
                    ratio_match = re.search(r'(\d+(?:\.\d+)?):1', text)
                    if ratio_match:
                        pattern_info['ratio'] = float(ratio_match.group(1))
                        print(f"Pattern ratio: {pattern_info['ratio']}:1")
                        
            # If we have a pattern name but no length, try to infer from known patterns
            if pattern_info['name'] and not pattern_info['length']:
                pattern_name_lower = pattern_info['name'].lower()
                for known_name, known_length in self.known_patterns.items():
                    if known_name in pattern_name_lower:
                        pattern_info['length'] = known_length
                        print(f"Inferred pattern length {known_length} from known pattern '{known_name}'")
                        break
        
        # If we still don't have pattern info, try multiple other methods
        if not pattern_info['name'] or not pattern_info['length']:
            # Method 1: Look for "OIL PATTERN INFO" section
            for heading in soup.find_all(['h2', 'h3', 'h4']):
                if 'oil pattern' in heading.text.lower() or 'lane condition' in heading.text.lower():
                    # Look at the text following this heading
                    pattern_text = ""
                    next_elem = heading.next_sibling
                    while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                        if hasattr(next_elem, 'text'):
                            pattern_text += next_elem.text + " "
                        next_elem = next_elem.next_sibling
                    
                    # Search for pattern name and length in this text
                    self._extract_pattern_from_text(pattern_text, pattern_info)
            
            # Method 2: Look for pattern info in tournament notes
            notes_keywords = ['tournament notes', 'event notes', 'notes']
            for keyword in notes_keywords:
                notes_elem = soup.find(string=re.compile(keyword, re.IGNORECASE))
                if notes_elem:
                    # Get the containing element and its text
                    parent = notes_elem.parent
                    notes_text = ""
                    # Try to get all text in the notes section
                    for sibling in parent.next_siblings:
                        if hasattr(sibling, 'text'):
                            notes_text += sibling.text + " "
                        if sibling.name in ['h2', 'h3', 'h4']:  # Stop at next heading
                            break
                    
                    # Extract pattern info from notes text
                    self._extract_pattern_from_text(notes_text, pattern_info)
            
            # Method 3: Look anywhere on the page for oil pattern mentions
            oil_pattern_texts = soup.find_all(string=re.compile(r'oil pattern|lane condition|pattern', re.IGNORECASE))
            for text_elem in oil_pattern_texts:
                if hasattr(text_elem.parent, 'text'):
                    self._extract_pattern_from_text(text_elem.parent.text, pattern_info)
        
        # As a last resort, try to infer from tournament name
        if tournament_name and (not pattern_info['name'] or not pattern_info['length']):
            tournament_lower = tournament_name.lower()
            
            # Look for known pattern names in tournament name
            for known_name, known_length in self.known_patterns.items():
                if known_name in tournament_lower:
                    if not pattern_info['name']:
                        pattern_info['name'] = known_name.title()
                        print(f"Inferred pattern name '{known_name}' from tournament name")
                    if not pattern_info['length']:
                        pattern_info['length'] = known_length
                        print(f"Inferred pattern length {known_length} from known pattern '{known_name}'")
                    break
            
            # Look for direct pattern specification like "Pattern 39" or "42 feet"
            pattern_spec_match = re.search(r'pattern\s+(\d{2})|(\d{2})\s*(?:ft|feet)', tournament_lower)
            if pattern_spec_match:
                length = pattern_spec_match.group(1) or pattern_spec_match.group(2)
                if length:
                    pattern_info['length'] = int(length)
                    print(f"Extracted pattern length {length} directly from tournament name")
        
        return pattern_info
    
    def _extract_pattern_from_text(self, text, pattern_info):
        """
        Extract pattern name and length from text
        """
        if not text:
            return
            
        # Clean up the text
        text = text.strip().lower()
        
        # Look for pattern name mentions in the format "Pattern: Name"
        pattern_name_match = re.search(r'pattern[:\s]+([a-z0-9\s]+)', text, re.IGNORECASE)
        if pattern_name_match and not pattern_info['name']:
            pattern_info['name'] = pattern_name_match.group(1).strip().title()
            print(f"Found pattern name in text: {pattern_info['name']}")
        
        # Look for pattern length mentions
        # Format like "45 feet" or "Length: 45 ft"
        length_match = re.search(r'(\d{2})\s*(?:ft|feet)', text)
        if length_match and not pattern_info['length']:
            pattern_info['length'] = int(length_match.group(1))
            print(f"Found pattern length in text: {pattern_info['length']} feet")
        
        # Look for pattern specifications like "Pattern Name 42" where 42 is the length
        if pattern_info['name']:
            # Look for a number after the pattern name
            pattern_with_length = re.search(
                pattern_info['name'].lower() + r'\s+(\d{2})', 
                text, 
                re.IGNORECASE
            )
            if pattern_with_length and not pattern_info['length']:
                pattern_info['length'] = int(pattern_with_length.group(1))
                print(f"Found pattern length after name: {pattern_info['length']} feet")
        
        # Look for common pattern names followed by numbers (like "Cheetah 35")
        for known_name in self.known_patterns.keys():
            if known_name in text:
                if not pattern_info['name']:
                    pattern_info['name'] = known_name.title()
                    print(f"Found known pattern name in text: {pattern_info['name']}")
                
                # Look for a number after the pattern name
                pattern_with_length = re.search(
                    known_name + r'\s+(\d{2})', 
                    text, 
                    re.IGNORECASE
                )
                if pattern_with_length and not pattern_info['length']:
                    pattern_info['length'] = int(pattern_with_length.group(1))
                    print(f"Found pattern length after known name: {pattern_info['length']} feet")
                
                # If we still don't have a length, use the default known length
                if not pattern_info['length']:
                    pattern_info['length'] = self.known_patterns[known_name]
                    print(f"Using default length for {known_name}: {pattern_info['length']} feet")
                
                break
    
    def scrape_year(self, year):
        """
        Scrapes all tournaments for a given year
        """
        tournaments = self.get_tournament_list(year)
        print(f"Found {len(tournaments)} tournaments for {year}")
        
        results = []
        
        for i, tournament in enumerate(tournaments):
            print(f"\nProcessing tournament {i+1}/{len(tournaments)}: {tournament['name']}")
            try:
                tournament_results = self.get_tournament_results(tournament['url'])
                if tournament_results:  # Only add if we got results
                    results.append(tournament_results)
                # Be nice to the server
                if i < len(tournaments) - 1:
                    print("Waiting 2 seconds before next request...")
                    time.sleep(2)
            except Exception as e:
                print(f"Error scraping {tournament['name']}: {str(e)}")
                
        return results

    def save_results(self, results, filename):
        """
        Saves results to JSON file
        """
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
            
    def save_to_csv(self, results, filename):
        """
        Converts results to a flat CSV format
        """
        if not results:
            print("No results to save to CSV")
            return
            
        rows = []
        for tournament in results:
            for result in tournament.get('results', []):
                row = {
                    'tournament_name': tournament.get('name', ''),
                    'start_date': tournament.get('start_date', ''),
                    'end_date': tournament.get('end_date', ''),
                    'center_name': tournament.get('center', {}).get('name', ''),
                    'center_location': tournament.get('center', {}).get('location', ''),
                    'pattern_name': tournament.get('pattern', {}).get('name', ''),
                    'pattern_length': tournament.get('pattern', {}).get('length', ''),
                    'pattern_volume': tournament.get('pattern', {}).get('volume', ''),
                    'pattern_ratio': tournament.get('pattern', {}).get('ratio', ''),
                }
                # Add all result fields
                for key, value in result.items():
                    row[key] = value
                    
                rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            print(f"Saved {len(rows)} results to {filename}")
        else:
            print("No rows to save to CSV")

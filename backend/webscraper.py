import os
import io
import time
import random
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fuzzywuzzy import process

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# URL Constants
BASE_URL = "https://fbref.com"
STANDINGS_URL = f"{BASE_URL}/en/comps/9/Premier-League-Stats"
TEAM_URL_PART = "/squads/"
SHOOTING_URL_PART = "all_comps/shooting/"

# File constants
DATA_DIR = "Data"
TEAM_MATCH_DATA_DIR = os.path.join(DATA_DIR, "Team Match Data")
AGGREGATED_FILE = os.path.join(DATA_DIR, "agg_match_data.csv")

# List of User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

class MissingDict(dict):
    __missing__ = lambda self, key: key

MAPPED_TEAM_NAMES = {
    "Brighton": "Brighton and Hove Albion",
    "Manchester Utd": "Manchester United",
    "Nott'ham Forest": "Nottingham Forest",
    "Newcastle Utd": "Newcastle United",
    "Tottenham": "Tottenham Hotspur",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers"
}

def get_headers(user_agent=None):
    """Generate headers, optionally keeping the same User-Agent."""
    if user_agent is None:
        user_agent = random.choice(USER_AGENTS)  # Choose a new one at the start

    return {
        "User-Agent": user_agent,
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": random.choice(["https://www.google.com/", "https://www.bing.com/"]),
        "DNT": "1",
        "Connection": "keep-alive",
    }

def make_request(session, url, retries=3):
    """Send a request with consistent User-Agent but header rotation, with retries for 429 or other transient errors."""
    user_agent = session.headers.get('User-Agent')
    session.headers.update(get_headers(user_agent))
    
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=10)
            
            # Check for 429 rate limit error
            if response.status_code == 429:
                logging.warning(f"Rate limit hit for {url}. Sleeping for {2**attempt} seconds...")
                time.sleep(2**attempt)  # Exponential backoff
                continue  # Retry after sleeping
            
            # Retry on server-side errors (5xx)
            if 500 <= response.status_code < 600:
                logging.warning(f"Server error for {url}. Retrying in {2**attempt} seconds...")
                time.sleep(2**attempt)
                continue
            
            response.raise_for_status()  # Raise an error for other bad status codes (4xx)
            return response
        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            return None
    
    logging.error(f"Exceeded max retries for {url}. Skipping...")
    return None

def check_data(data, error_message):
    """Helper function to check if data is valid."""
    if not data:
        logging.error(error_message)
        return False
    return True
    
def process_team_input(team_input, team_names):
    """Matches user input to valid team names using fuzzy matching."""
    selected_teams = [team.strip().lower() for team in team_input.split(",")]
    matched_teams = []

    for input_team in selected_teams:
        match = process.extractOne(input_team, team_names)
        if match:
            best_match, score = match
            if score > 80:
                matched_teams.append(best_match)
            else:
                logging.warning(f"'{input_team}' did not match any known team (Best match: {best_match} - {score}%).")
        else:
            logging.warning(f"No close match found for '{input_team}'. Skipping.")

    return matched_teams if matched_teams else None

def scrape_team_data(team_url, team_name, session):
    """Scrapes team match data."""
    logging.info(f"Scraping data for {team_name}...")

    # Get team match data
    team_data_page = make_request(session, team_url)
    if not check_data(team_data_page, f"Request failed for {team_name}."):
        return pd.DataFrame()

    match_dfs = pd.read_html(io.StringIO(team_data_page.text), match="Scores & Fixtures")
    if not check_data(match_dfs, f"No match data found for {team_name}, skipping..."):
        return pd.DataFrame()

    match_dataframe = match_dfs[0]
    soup = BeautifulSoup(team_data_page.text, "html.parser")

    # Get the team logo URL from the team page
    image_tag = soup.find("img", class_="teamlogo")
    team_logo_url = image_tag["src"] if image_tag else ""

    # Get shooting data from the team page
    team_data_links = [l.get("href") for l in soup.find_all('a')]
    shooting_links = [l for l in team_data_links if l and SHOOTING_URL_PART in l]
    if not check_data(shooting_links, f"No shooting data found for {team_name}. Skipping shooting stats..."):
        return pd.DataFrame()

    shooting_data = make_request(session, f"{BASE_URL}{shooting_links[0]}")
    if not check_data(shooting_data, f"Request failed for {team_name}."):
        return pd.DataFrame()
    
    shooting_dfs = pd.read_html(io.StringIO(shooting_data.text), match="Shooting")
    if not check_data(shooting_dfs, f"Could not find shooting data for {team_name}, skipping..."):
        return pd.DataFrame()

    shooting_dataframe = shooting_dfs[0]
    shooting_dataframe.columns = shooting_dataframe.columns.droplevel()

    try:
        team_data = match_dataframe.merge(shooting_dataframe[["Date", "Sh", "SoT", "FK", "PKatt"]], on="Date")
    except ValueError:
        logging.error(f"Error merging data for {team_name}. Skipping...")
        return pd.DataFrame()
    
    # Filter to Premier League matches
    team_data = team_data[team_data["Comp"] == "Premier League"]

    # Add team name and logo url columns
    team_data["Team"] = team_name
    team_data["Logo"] = team_logo_url

    # Map opponent team names to the full team name (Wolves -> Wolverhamptoon Wanderers)
    team_data["Opponent"] = team_data["Opponent"].apply(lambda x: MissingDict(**MAPPED_TEAM_NAMES)[x])

    # Drop unnecessary columns
    team_data.drop(columns=[
        "Time", "Day", "Comp", "Round", "Attendance", "Captain", "Formation", "Opp Formation", "Referee", "Match Report", "Notes"
    ], inplace=True)

    return team_data

def aggregate_data(data_dir, output_file):
    """Aggregates all team CSV files into one dataset."""
    logging.info("Aggregating data...")
    all_team_data = []

    # Loop through all CSV files in the Team Data folder
    for file_name in os.listdir(data_dir):
        if file_name.endswith(".csv"):
            team_data_path = os.path.join(data_dir, file_name)
            logging.info(f"Reading data from {team_data_path}...")
            team_data = pd.read_csv(team_data_path)
            all_team_data.append(team_data)

    # Concatenate all team data into one DataFrame and save as single csv file
    if all_team_data:
        final_data = pd.concat(all_team_data, ignore_index=True)
        final_data.index.name = "ID"
        final_data.to_csv(output_file)
        logging.info(f"Aggregated data saved to {output_file}")
    else:
        logging.error("No data to aggregate.")

def main():
    # Ask user if they want to scrape, aggregate, or both
    action = input("Enter 'scrape' to scrape new data, 'aggregate' to aggregate existing data, or 'both' for both: ").strip().lower()
    do_scrape = action in ('scrape', 'both')
    do_aggregate = action in ('aggregate', 'both')

    # Ensure folders exists for output
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(TEAM_MATCH_DATA_DIR, exist_ok=True)

    if do_scrape:
        # Create a session
        session = requests.Session()
        session.headers.update(get_headers())

        # Get the HTML from the standings page
        standings_page = make_request(session, STANDINGS_URL)
        if not check_data(standings_page, "Request failed. Check the URL or retry after some time in case of temporary IP blocking. Exiting..."):
            exit()

        soup = BeautifulSoup(standings_page.text, "html.parser")

        # Get the standings table
        standings_table = soup.select_one('table.stats_table')
        if not check_data(standings_table, "Standings table not found. The page structure might have changed. Exiting..."):
            exit()

        # Extract links to team stats pages
        team_links = [l.get("href") for l in standings_table.find_all('a')]
        team_urls = [l for l in team_links if TEAM_URL_PART in l]
        absolute_team_urls = [f"{BASE_URL}{t}" for t in team_urls]

        # Extract clean team names
        team_names = [url.split("/")[-1].replace("-Stats", "").replace("-", " ") for url in absolute_team_urls]

        # Prompt the user for team selection
        team_input = input("Enter team names to scrape (comma-separated, or leave blank for all teams): ").strip().lower()

        if team_input:
            matched_teams = process_team_input(team_input, team_names)

            if not check_data(matched_teams, "No valid teams found. Exiting..."):
                exit()

            # Filter URLs and teams to just those that match the input
            team_names = matched_teams
            matched_teams_lower = {name.lower() for name in matched_teams}
            absolute_team_urls = [url for url, name in zip(absolute_team_urls, team_names) if name.lower() in matched_teams_lower]
            
            logging.info(f"Scraping data for selected teams: {', '.join(team_names)}")
        else:
            logging.info("Scraping data for all teams.")

        for i, (team_url, team_name) in enumerate(zip(absolute_team_urls, team_names)):
            team_data = scrape_team_data(team_url, team_name, session)
            if not team_data.empty:
                # Define the output file path
                output_file = os.path.join(TEAM_MATCH_DATA_DIR, f"{team_name.replace(' ', '_')}_match_data.csv")

                # Save the data for the current team to a CSV, overwriting if the file already exists
                team_data.to_csv(output_file, index=False)
                logging.info(f"Data saved for {team_name} to {output_file}")

            # Random sleep to prevent blocking
            if i < len(team_names) - 1:
                sleep_time = random.uniform(10, 20)
                logging.info(f"Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

        logging.info("Scraping completed.")

    if do_aggregate:
        aggregate_data(TEAM_MATCH_DATA_DIR, AGGREGATED_FILE)

if __name__ == "__main__":
    main()
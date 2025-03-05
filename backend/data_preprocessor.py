import os
import logging
import pandas as pd

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File constants
DATA_DIR = "Data"
TEAM_DATA_FILE = os.path.join(DATA_DIR, "team_data.csv")
TRAINING_DATA_FILE = os.path.join(DATA_DIR, "training_data.csv")
AGGREGATED_FILE = os.path.join(DATA_DIR, "agg_match_data.csv")

def load_data(file_path):
    """Load CSV data into a pandas DataFrame."""
    try:
        data = pd.read_csv(file_path, index_col=0)
        logging.info(f"Successfully loaded data from {file_path}")
        return data
    except Exception as e:
        logging.error(f"Error loading data from {file_path}: {e}")
        return None

def clean_data(data):
    """Clean match data by converting date and categorical variables."""
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.sort_values("Date")
    data["Result"] = data["Result"].map({"W": 2, "D": 1, "L": 0})
    data["Venue"] = data["Venue"].map({"Home": 0, "Away": 1})
    data["Team_code"] = data["Team"].astype("category").cat.codes
    return data

def rolling_averages(group, cols):
    """Compute rolling averages for performance stats."""
    group = group.sort_values("Date")
    return group.assign(**{f"{col}_rolling": group[col].rolling(window=5, min_periods=3, closed='left').mean() for col in cols})

def cumulative_stats(group):
    """Compute cumulative goal differential and win/draw/loss percentages."""
    group = group.sort_values("Date")
    group["GD"] = (group["GF"] - group["GA"]).expanding().sum().shift(1)
    for result, label in zip([2, 1, 0], ["Win%", "Draw%", "Loss%"]):
        group[label] = (group["Result"] == result).expanding().mean().shift(1)
    return group

def merge_match_data(home_data, away_data, rolling_cols):
    """Merge Home and Away team stats into a single row per match."""
    merged_data = home_data.merge(
        away_data,
        left_on=["Date", "Team"],
        right_on=["Date", "Opponent"],
        suffixes=("_home", "_away"),
        how="inner" 
    )
    merged_data = merged_data[[
        "Date", "Result_home", "Team_home", "Team_code_home", "Opponent_home", "Team_code_away"
    ] + [col + "_rolling_home" for col in rolling_cols] + [col + "_rolling_away" for col in rolling_cols] + [
        "GD_home", "Win%_home", "Draw%_home", "Loss%_home",
        "GD_away", "Win%_away", "Draw%_away", "Loss%_away"
    ]]
    return merged_data.rename(columns={
        'Result_home': 'Match_Result', 'Team_home': 'Home_Team', 'Opponent_home': 'Away_Team',
        'Team_code_home': 'Home_Team_code', 'Team_code_away': 'Away_Team_code'
    }).sort_values("Date")

def save_data(data, file_path):
    """Save DataFrame to a CSV file."""
    try:
        data.to_csv(file_path, index=False)
        logging.info(f"Data successfully saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving data to {file_path}: {e}")

def final_rolling_average(group, cols):
    """Compute rolling averages based on the last 5 matches."""
    group = group.sort_values("Date")
    rolling_cols = [f"{col}_rolling" for col in cols]
    group[rolling_cols] = group[cols].rolling(window=5, min_periods=3, closed='right').mean()
    return group[rolling_cols].iloc[-1]  # Get the last available rolling average

def final_cumulative_stats(group):
    """Compute cumulative stats based on all available matches."""
    group = group.sort_values("Date")
    total_gd = (group["GF"] - group["GA"]).sum()
    total_W = (group["Result"] == 2).sum()
    total_D = (group["Result"] == 1).sum()
    total_L = (group["Result"] == 0).sum()
    
    win_percentage = (group["Result"] == 2).mean()
    draw_percentage = (group["Result"] == 1).mean()
    loss_percentage = (group["Result"] == 0).mean()
    
    return pd.Series({
        "GD": total_gd,
        "Wins": total_W,
        "Draws": total_D,
        "Losses": total_L,
        "Win%": win_percentage,
        "Draw%": draw_percentage,
        "Loss%": loss_percentage
    })

def main():
    # Load and clean data
    match_data = load_data(AGGREGATED_FILE)
    if match_data is not None:
        match_data = clean_data(match_data)

        cols_to_roll = ["GF", "GA", "xG", "xGA", "Poss", "Sh", "SoT", "FK", "PKatt"]
        match_data_rolling = match_data.groupby("Team", group_keys=False).apply(rolling_averages, cols_to_roll)
        match_data_rolling = match_data_rolling.groupby("Team", group_keys=False).apply(cumulative_stats).dropna()

        # Split into Home and Away team data and merge
        home_match_data = match_data_rolling[match_data_rolling["Venue"] == 0].copy()
        away_match_data = match_data_rolling[match_data_rolling["Venue"] == 1].copy()
        merged_match_data = merge_match_data(home_match_data, away_match_data, cols_to_roll)

        # Save cleaned match data
        save_data(merged_match_data, TRAINING_DATA_FILE)

        # Compute rolling averages and cumulative stats for each team
        team_stats = match_data.groupby("Team").apply(lambda group: pd.concat([
            final_rolling_average(group, cols_to_roll),
            final_cumulative_stats(group)
        ], axis=0), include_groups=False)
        team_codes = match_data[["Team_code", "Team", "Logo"]].drop_duplicates()
        team_data = team_codes.merge(team_stats, on="Team").sort_values("Team_code").rename(columns={"Team": "Team_Name", "Team_code": "Team_Code"})
        
        # Save team data
        save_data(team_data, TEAM_DATA_FILE)

if __name__ == "__main__":
    main()
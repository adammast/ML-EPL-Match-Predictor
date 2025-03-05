import os
import joblib
import pandas as pd
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

# File constants
DATA_DIR = "Data"
TEAM_DATA_FILE = os.path.join(DATA_DIR, "team_data.csv")
MODEL_FILE = "xgb_model.pkl"

app = Flask(__name__)
CORS(app)

def load_model():
    """Load and return the trained model."""
    if not os.path.exists(MODEL_FILE):
        abort(500, "Model file not found. Train the model first.")
    return joblib.load(MODEL_FILE)

def load_team_data():
    """Load and return team data as a DataFrame."""
    if not os.path.exists(TEAM_DATA_FILE):
        abort(500, "Team data file not found.")
    return pd.read_csv(TEAM_DATA_FILE)

# Load model and team data
model = load_model()
team_data = load_team_data()

@app.route("/teams", methods=["GET"])
def get_teams():
    """Returns all team names along with their logo URLs, records, and last 5 matches."""
    teams_list = []

    for _, row in team_data.iterrows():
        team_info = {
            "team_name": row["Team_Name"],
            "logo_url": row["Logo"],
            "wins": int(row["Wins"]),
            "draws": int(row["Draws"]),
            "losses": int(row["Losses"]),
            "goal_differential": int(row["GD"]),
            "last_5_matches": [] # Placeholder, can be updated with actual match history
        }

        teams_list.append(team_info)

    return jsonify({"teams": teams_list})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    if not data or "home_team" not in data or "away_team" not in data:
        abort(400, "Both 'home_team' and 'away_team' must be provided.")
    
    # Get team data from team name
    home_team_data = team_data.loc[team_data["Team_Name"] == data.get("home_team")]
    away_team_data = team_data.loc[team_data["Team_Name"] == data.get("away_team")]

    # Ensure team data exists
    if home_team_data.empty or away_team_data.empty:
         abort(400, "One or both teams not found in team_data.csv")

    # Convert Team_Code to int
    home_team_code = int(home_team_data["Team_Code"].values[0])
    away_team_code = int(away_team_data["Team_Code"].values[0])

    # Extract rolling averages and cumulative stats for both teams
    rolling_avg_cols = [
        "GF_rolling", "GA_rolling", "xG_rolling", "xGA_rolling",
        "Poss_rolling", "Sh_rolling", "SoT_rolling", "FK_rolling", "PKatt_rolling"
    ]
    cumulative_cols = ["GD", "Win%", "Draw%", "Loss%"]

    home_rolling_avg = home_team_data[rolling_avg_cols].astype(float).values[0]
    home_cumulative = home_team_data[cumulative_cols].astype(float).values[0]

    away_rolling_avg = away_team_data[rolling_avg_cols].astype(float).values[0]
    away_cumulative = away_team_data[cumulative_cols].astype(float).values[0]

    # Create feature dictionary
    features_dict = {
        "Home_Team_code": home_team_code,
        "Away_Team_code": away_team_code
    }

    # Add rolling average and cumulative stats for home and away teams
    for i, col in enumerate(rolling_avg_cols):
        features_dict[f"{col}_home"] = home_rolling_avg[i]

    for i, col in enumerate(cumulative_cols):
        features_dict[f"{col}_home"] = home_cumulative[i]

    for i, col in enumerate(rolling_avg_cols):
        features_dict[f"{col}_away"] = away_rolling_avg[i]

    for i, col in enumerate(cumulative_cols):
        features_dict[f"{col}_away"] = away_cumulative[i]

    # Create DataFrame from extracted data
    features = pd.DataFrame([features_dict])

    try:
        probabilities = model.predict_proba(features)[0]
        response = {
            "home_win": round(float(probabilities[2]) * 100, 2),
            "draw": round(float(probabilities[1]) * 100, 2),
            "away_win": round(float(probabilities[0]) * 100, 2),
        }
    except Exception as e:
        abort(500, f"Prediction failed: {str(e)}")

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
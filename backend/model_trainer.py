import os
import joblib
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File constants
DATA_DIR = "Data"
TRAINING_DATA_FILE = os.path.join(DATA_DIR, "training_data.csv")
MODEL_FILE = "xgb_model.pkl"

# Model Hyperparameters
XGB_PARAMS = {
    "n_estimators": 50,
    "max_depth": 1,
    "learning_rate": 0.1,
    "eval_metric": "logloss"
}

def load_training_data(file_path):
    """Load and validate training data from CSV."""
    try:
        data = pd.read_csv(file_path, index_col=0)
        logging.info(f"Successfully loaded training data from {file_path}")
        return data
    except Exception as e:
        logging.error(f"Error loading training data: {e}")
        return None

def get_features_and_target(data):
    """Prepare features and target variable for training."""
    base_features = ["Home_Team_code", "Away_Team_code"]
    home_features = [
        "GF_rolling_home", "GA_rolling_home", "xG_rolling_home", "xGA_rolling_home", 
        "Poss_rolling_home", "Sh_rolling_home", "SoT_rolling_home", "FK_rolling_home", "PKatt_rolling_home",
        "GD_home", "Win%_home", "Draw%_home", "Loss%_home"
    ]
    away_features = [
        "GF_rolling_away", "GA_rolling_away", "xG_rolling_away", "xGA_rolling_away", 
        "Poss_rolling_away", "Sh_rolling_away", "SoT_rolling_away", "FK_rolling_away", "PKatt_rolling_away",
        "GD_away", "Win%_away", "Draw%_away", "Loss%_away"
    ]
    
    all_features = base_features + home_features + away_features

    return data[all_features], data["Match_Result"]

def train_model(x_train, y_train, params):
    """Train an XGBoost model and return it."""
    model = XGBClassifier(**params)
    model.fit(x_train, y_train)
    return model

def evaluate_model(model, x_test, y_test):
    """Evaluate the model and log accuracy."""
    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    logging.info(f"XGBoost Model Accuracy: {accuracy:.2f}")
    return accuracy

def save_model(model, file_path):
    """Save trained model to file."""
    try:
        joblib.dump(model, file_path)
        logging.info(f"Model saved as {file_path}")
    except Exception as e:
        logging.error(f"Error saving model: {e}")

def main():
    """Main training pipeline."""
    training_data = load_training_data(TRAINING_DATA_FILE)
    if training_data is None:
        return
    
    # Train model
    feature_matrix, target = get_features_and_target(training_data)
    x_train, x_test, y_train, y_test = train_test_split(feature_matrix, target, test_size=0.2)
    xgb_model = train_model(x_train, y_train, XGB_PARAMS)

    evaluate_model(xgb_model, x_test, y_test)
    save_model(xgb_model, MODEL_FILE)

if __name__ == "__main__":
    main()
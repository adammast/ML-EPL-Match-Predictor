# EPL Match Predictor

## Overview

This project is a machine learning-based web application that predicts match outcomes for the English Premier League. It gathers and processes match data using web scraping, trains an XGBoost model, and provides a Vue.js-based UI for users to make predictions.

## Features

- **Web Scraping**: Extracts match and team data from an online source.
- **Data Processing**: Prepares and structures the scraped data for training.
- **Machine Learning Model**: Trains an XGBoost model for match outcome predictions.
- **REST API Backend**: A Flask API serves predictions and team data.
- **Web UI**: A Vue.js frontend allows users to select teams and view predictions.

## File Structure

```
ML EPL Match Predictor
│── backend
│   ├── Data/                # Contains raw and processed match data
│   ├── data_preprocessor.py # Prepares training data
│   ├── model_trainer.py     # Trains the machine learning model
│   ├── predictor.py         # Flask API for predictions
│   ├── webscraper.py        # Scrapes match and team data
│   ├── xgb_model.pkl        # Trained machine learning model
│── frontend/                # Vue.js frontend
│── README.md
```

## Installation and Setup

### Prerequisites

Ensure you have the following installed:

- Python 3.8+
- Node.js & npm
- Required Python packages:
  ```bash
  pip install -r requirements.txt
  ```

### Running the Backend

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Run the Flask API:
   ```bash
   python predictor.py
   ```

### Running the Frontend

1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run serve
   ```
4. Open `http://localhost:8080/` in your browser.

## How It Works

### 1. Web Scraping (`webscraper.py`)

- Scrapes match data and stores it in team-specific CSV files.
- Aggregates all data into `agg_match_data.csv`.
- Usage:
  ```bash
  python webscraper.py
  ```

### 2. Data Preprocessing (`data_preprocessor.py`)

- Converts raw match data into training-ready datasets.
- Generates `training_data.csv` and `team_data.csv`.
- Usage:
  ```bash
  python data_preprocessor.py
  ```

### 3. Model Training (`model_trainer.py`)

- Uses `training_data.csv` to train an XGBoost model.
- Saves the trained model as `xgb_model.pkl`.
- Outputs model accuracy.
- Usage:
  ```bash
  python model_trainer.py
  ```

### 4. Prediction API (`predictor.py`)

- Serves predictions and team data via a REST API.
- Usage:
  ```bash
  python predictor.py
  ```
- API Endpoints:
  - `GET /teams` - Returns a list of teams with records and logos.
  - `POST /predict` - Predicts match outcomes based on selected teams.

## Usage

- Start both backend and frontend.
- Select a home and away team on the UI.
- Click "Predict Match Outcome" to view prediction probabilities.

## Included Example Data

For convenience, the repository includes pre-generated data files and a trained model. Users can run the UI without running the scripts manually.

## Technologies Used

- **Python** (Flask, Pandas, BeautifulSoup, XGBoost)
- **JavaScript** (Vue.js, Axios)
- **Machine Learning** (XGBoost Classifier)

## License

This project is licensed under the MIT License.

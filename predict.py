from nba_api.stats.static import teams
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import joblib
import pandas as pd

load_dotenv()

# Load the trained model
model = joblib.load('basketball_prediction_model.joblib')

def predict_winner(first_team, second_team):
    # Find the teams using NBA API
    matching_teams1 = teams.find_teams_by_full_name(first_team)
    matching_teams2 = teams.find_teams_by_full_name(second_team)
    error_message = "Team not found"

    # Check for team existence
    if not matching_teams1:
        print(error_message, first_team)
        return error_message, None, None
    if not matching_teams2:
        print(error_message, second_team)
        return error_message, None, None

    # Get team information
    team_info1 = matching_teams1[0]
    team_info2 = matching_teams2[0]
    team_id1 = team_info1['id']
    team_id2 = team_info2['id']
    
    # Connect to MongoDB to retrieve game-level stats
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client['basketball_data']
    games_collection = db['games']

    # Retrieve the last 10 games data for each team
    team1_games = list(games_collection.find({'TEAM_ID': team_id1}).sort("GAME_DATE", -1).limit(30))
    team2_games = list(games_collection.find({'TEAM_ID': team_id2}).sort("GAME_DATE", -1).limit(30))

    # Define features to retrieve
    features = ['PTS', 'FGM', 'FG_PCT', 'FG3M', 'FG3_PCT', 'DREB', 'PLUS_MINUS']
    if len(team1_games) < 10 or len(team2_games) < 10:
        return "Prediction error", None, None

    # Calculate average of features for the last 10 games
    team1_averages = {feature: sum(game[feature] for game in team1_games) / 30 for feature in features}
    team2_averages = {feature: sum(game[feature] for game in team2_games) / 30 for feature in features}

    # Calculate differences between average features for prediction
    feature_diffs = {f"{feature}": team1_averages[feature] - team2_averages[feature] for feature in features}
    feature_diffs_df = pd.DataFrame([feature_diffs])  # Create a DataFrame for model input
    print(feature_diffs_df)
    # Predict the outcome based on feature differences
    prediction = model.predict(feature_diffs_df)
    probability = model.predict_proba(feature_diffs_df)
    if prediction[0] == 1:
        return team_info1['full_name'], team_info2['full_name'], probability[0][1]
    else:
        return team_info2['full_name'], team_info1['full_name'], probability[0][0]

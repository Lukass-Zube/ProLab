import joblib
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from predict import predict_winner
from helper.custom_errors import TeamNotFoundError, NotEnoughGamesError
from sklearn.metrics import mean_squared_error
import numpy as np

# Load environment variables
load_dotenv()

model = joblib.load('basketball_prediction_model.joblib')

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['games']

# Query the last 100 data points (50 games) from MongoDB
last_games = list(collection.find().sort("GAME_DATE", -1).limit(100))

# Group games by GAME_ID
games_dict = {}
for game in last_games:
    game_id = game['GAME_ID']
    if game_id not in games_dict:
        games_dict[game_id] = []
    games_dict[game_id].append(game)

# Prepare matchups
matchups = []
for game_id, games in games_dict.items():
    if len(games) == 2:  # Ensure there are two entries for each game
        team1 = games[0]['TEAM_NAME']  # Replace with actual team ID field
        team1_score = games[0]['PTS']  # Replace with actual score field
        team2 = games[1]['TEAM_NAME']  # Replace with actual team ID field
        team2_score = games[1]['PTS']  # Replace with actual score field
        
        # Append the matchup
        matchups.append((team1, team1_score, team2, team2_score))

# Check if there are enough matchups
if len(matchups) < 1:
    raise NotEnoughGamesError("Not enough games found in the database.", 2)

# Lists to store actual and predicted scores
actual_scores = []
predicted_scores = []

# Use the predict_winner function for each matchup
for first_team, first_team_score, second_team, second_team_score in matchups:
    try:
        first_team_name, predicted_first_score, second_team_name, predicted_second_score = predict_winner(
            first_team, second_team, model, db  # Pass model if needed
        )
        
        # Store actual and predicted scores
        actual_scores.append(first_team_score)  # Actual score for first team
        actual_scores.append(second_team_score)  # Actual score for second team
        predicted_scores.append(predicted_first_score)  # Predicted score for first team
        predicted_scores.append(predicted_second_score)  # Predicted score for second team
        
        print(f"{first_team_name}, Pred score: {predicted_first_score}, Real score: {first_team_score}, {second_team_name} Pred score: {predicted_second_score}, Real score: {second_team_score}")
    except TeamNotFoundError as e:
        print(f"Error: {str(e)}")
    except NotEnoughGamesError as e:
        print(f"Error: {str(e)}")

# Calculate RMSE
rmse = np.sqrt(mean_squared_error(actual_scores, predicted_scores))
print(f"Root Mean Square Error: {rmse:.2f}")


import os
from dotenv import load_dotenv
import joblib
from nba_api.stats.static import teams
import pandas as pd
from pymongo import MongoClient
from helper.custom_errors import TeamNotFoundError, NotEnoughGamesError


def predict_winner(first_team, second_team, model, db, num_games=10):
    # Find the teams using NBA API
    matching_teams1 = teams.find_teams_by_full_name(first_team)
    matching_teams2 = teams.find_teams_by_full_name(second_team)

    # Check for team existence
    if not matching_teams1:
        raise TeamNotFoundError(first_team)
    if not matching_teams2:
        raise TeamNotFoundError(second_team)

    # Get team information
    team_info1 = matching_teams1[0]
    team_info2 = matching_teams2[0]
    team_id1 = team_info1['id']
    team_id2 = team_info2['id']

    games_collection = db['games']

    # Retrieve the last num_games games for each team
    team1_games = list(games_collection.find({
        'TEAM_ID': team_id1
    }).sort("GAME_DATE", -1).limit(num_games))

    team2_games = list(games_collection.find({
        'TEAM_ID': team_id2
    }).sort("GAME_DATE", -1).limit(num_games))

    if (len(team1_games) != num_games):
        raise NotEnoughGamesError(first_team, num_games)
    elif (len(team2_games) != num_games):
        raise NotEnoughGamesError(second_team, num_games)

    # Define features to retrieve
    features = [
    'MIN',
    # 'PTS',
    'FGM',
    'FG_PCT',
    'FGA',
    'FG3M',
    'FG3A',
    'FG3_PCT',
    'FTM',
    'FTA',
    'FT_PCT',
    'OREB',
    'DREB',
    'REB',
    'AST',
    'STL',
    'BLK',
    'TOV',
    'PF',
    'PLUS_MINUS']

    teams_collection = db['teams']

    def calculate_weighted_averages(games, team_id):
        total_weight = 0
        weighted_averages = {feature: 0 for feature in features}
        
        for game in games:
            game_id = game['GAME_ID']
            game_details = games_collection.find_one({'GAME_ID': game_id, 'TEAM_ID': {'$ne': team_id}})
            opponent_id = game_details['TEAM_ID']
            
            opponent_master_rank = teams_collection.find_one({'TEAM_ID': opponent_id})['MASTER_RANK']
            
            # Calculate weight based on opponent's MASTER_RANK
            weight = 1 / opponent_master_rank if opponent_master_rank != 0 else 1  # Avoid division by zero
            
            # Accumulate weighted averages
            for feature in features:
                weighted_averages[feature] += game[feature] * weight
            
            total_weight += weight
        
        # Finalize the weighted averages
        if total_weight > 0:
            for feature in features:
                weighted_averages[feature] /= total_weight
        
        return weighted_averages

# Calculate average of features for the last 10 games with weighting
    team1_averages = calculate_weighted_averages(team1_games, team_id1)
    team1_averages['TEAM_ID'] = team_id1

    team2_averages = calculate_weighted_averages(team2_games, team_id2)
    team2_averages['TEAM_ID'] = team_id2

    # Calculate average of features for the last 10 games
    # team1_averages = {feature: sum(game[feature] for game in team1_games) / len(team1_games) for feature in features}
    # team1_averages['TEAM_ID'] = team_id1
    # print(team1_averages)
    
    # team2_averages = {feature: sum(game[feature] for game in team2_games) / len(team2_games) for feature in features}
    # team2_averages['TEAM_ID'] = team_id2
    # print(team2_averages)

    # Calculate differences between average features for prediction
    feature_diffs1 = {f"{feature}": team1_averages[feature] for feature in features}
    feature_diffs1['TEAM_ID'] = team1_averages['TEAM_ID']  # Add TEAM_ID to the dictionary
    feature_diffs1_df = pd.DataFrame([feature_diffs1])  # Create a DataFrame for model input

    feature_diffs2 = {f"{feature}": team2_averages[feature] for feature in features}
    feature_diffs2['TEAM_ID'] = team2_averages['TEAM_ID']  # Add TEAM_ID to the dictionary
    feature_diffs2_df = pd.DataFrame([feature_diffs2])  # Create a DataFrame for model input

    # Predict the scores for each team
    team1_score = model.predict(feature_diffs1_df)[0]
    team2_score = model.predict(feature_diffs2_df)[0]

    # Round the predicted scores to whole numbers
    team1_score = round(team1_score)
    team2_score = round(team2_score)
    # Return team names and predicted scores
    return team_info1['full_name'], team1_score, team_info2['full_name'], team2_score

def test_predict_game():

    load_dotenv()

    model = joblib.load('basketball_prediction_model.joblib')
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client['basketball_data']


    # Mock team IDs for testing
    team_name1 = "Atlanta Hawks"
    team_name2 = "Boston Celtics"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db)
    print(team1_name, team1_score, team2_name, team2_score)
    # Basic assertions

    team_name1 = "Miami Heat"
    team_name2 = "Charlotte Hornets"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db)
    print(team1_name, team1_score, team2_name, team2_score)

    team_name1 = "Charlotte Hornets"
    team_name2 = "Miami Heat"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db)
    print(team1_name, team1_score, team2_name, team2_score)


if __name__ == "__main__":
    test_predict_game()

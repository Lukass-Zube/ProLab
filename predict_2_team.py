import os
from dotenv import load_dotenv
import joblib
from nba_api.stats.static import teams
import pandas as pd
from pymongo import MongoClient
from helper.custom_errors import TeamNotFoundError, NotEnoughGamesError


def predict_winner(first_team, second_team, model, db, num_games=10, home_advantage=1):
    #home advantage is 1 for 1st team, 0 for 2nd team
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
        HOME_ADVANTAGE_MULTIPLIER = 0.05  # 5% adjustment for home/away games
        total_weight = 0
        weighted_averages = {feature: 0 for feature in features}
        
        for game in games:
            game_id = game['GAME_ID']
            game_details = games_collection.find_one({'GAME_ID': game_id, 'TEAM_ID': {'$ne': team_id}})
            opponent_id = game_details['TEAM_ID']
            opponent_master_rank = teams_collection.find_one({'TEAM_ID': opponent_id})['MASTER_RANK']
            
            # Calculate weight based on opponent's MASTER_RANK
            if (game['WL']=="W"):
                team_won = True
                weight = 1 / opponent_master_rank if opponent_master_rank != 0 else 1  # Avoid division by zero
            else:
                team_won = False
                weight = 1 - 1 / opponent_master_rank if opponent_master_rank != 0 else 1  # Avoid division by zero
            
            # Determine if it was a home game
            game_stats = game.copy()


            matchup = game['MATCHUP']

            # '@' in matchup means away game, 'vs.' means home game
            home_advantage_in_game = 1 if 'vs.' in matchup else 0
            
            # Adjust statistics based on home/away to normalize the advantage
            for feature in features:
                if feature in ['MIN', 'FG_PCT', 'FG3_PCT', 'FT_PCT']:  # Skip percentage stats
                    continue
                if home_advantage_in_game:
                    # If it was a home game, reduce the stats to normalize
                    game_stats[feature] = game[feature] * (1 - HOME_ADVANTAGE_MULTIPLIER)
                else:
                    # If it was an away game, increase the stats to normalize
                    game_stats[feature] = game[feature] * (1 + HOME_ADVANTAGE_MULTIPLIER)
            
            # Accumulate weighted averages using adjusted stats
            for feature in features:
                weighted_averages[feature] += game_stats[feature] * weight
            
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

    team1_master_rank = teams_collection.find_one({'TEAM_ID': team_id1})['MASTER_RANK']
    team2_master_rank = teams_collection.find_one({'TEAM_ID': team_id2})['MASTER_RANK']

    # Calculate rank-based adjustment multipliers
    RANK_ADJUSTMENT_FACTOR = 0.005  # 0.5% maximum adjustment per rank difference
    MAX_ADJUSTMENT = 0.05  # 5% maximum total adjustment
    
    rank_difference = team2_master_rank - team1_master_rank
    adjustment = min(abs(rank_difference) * RANK_ADJUSTMENT_FACTOR, MAX_ADJUSTMENT)
    
    if rank_difference > 0:  # team1 is better ranked
        team1_multiplier = 1 + adjustment
        team2_multiplier = 1 - adjustment
    else:  # team2 is better ranked
        team1_multiplier = 1 - adjustment
        team2_multiplier = 1 + adjustment

    # Apply rank-based adjustments to averages
    for feature in features:
        if feature not in ['MIN', 'FG_PCT', 'FG3_PCT', 'FT_PCT']:  # Skip percentage stats
            team1_averages[feature] *= team1_multiplier
            team2_averages[feature] *= team2_multiplier

    # Calculate differences between average features for prediction
    combined_features = {}

    # Add team 1 features with TEAM1_ prefix
    for feature in features:
        combined_features[f"TEAM1_{feature}"] = team1_averages[feature]
    combined_features['TEAM1_ID'] = team1_averages['TEAM_ID']
    combined_features['TEAM1_HOME_ADVANTAGE'] = home_advantage

    # Add team 2 features with TEAM2_ prefix
    for feature in features:
        combined_features[f"TEAM2_{feature}"] = team2_averages[feature]
    combined_features['TEAM2_ID'] = team2_averages['TEAM_ID']
    combined_features['TEAM2_HOME_ADVANTAGE'] = not home_advantage

    # Create a single DataFrame with all features
    combined_df = pd.DataFrame([combined_features])

    # Make a single prediction that returns both scores
    predicted_scores = model.predict(combined_df)[0]

    # Prevent draws by adding 1 to the higher decimal when rounded scores would be equal
    if round(predicted_scores[0]) == round(predicted_scores[1]):
        if predicted_scores[0] > predicted_scores[1]:
            team1_score = round(predicted_scores[0])
            team2_score = round(predicted_scores[1]) - 1
        else:
            team1_score = round(predicted_scores[0]) - 1
            team2_score = round(predicted_scores[1])
    else:
        team1_score = round(predicted_scores[0])
        team2_score = round(predicted_scores[1])

    # Return team names and predicted scores
    return team_info1['full_name'], team1_score, team_info2['full_name'], team2_score

def test_predict_game():

    load_dotenv()

    model = joblib.load('basketball_prediction_model_2_team.joblib')
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client['basketball_data']

    num_games = 5
    # Mock team IDs for testing
    # team_name1 = "Toronto Raptors"
    # team_name2 = "Cleveland Cavaliers"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)
    # Basic assertions

    # team_name1 = "Golden State Warriors"
    # team_name2 = "Detroit Pistons"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)

    # team_name1 = "Minnesota Timberwolves"
    # team_name2 = "Orlando Magic"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)

    # team_name1 = "Portland Trail Blazers"
    # team_name2 = "Dallas Mavericks"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)

    # team_name1 = "Houston Rockets"
    # team_name2 = "Memphis Grizzlies"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)

    # team_name1 = "Atlanta Hawks"
    # team_name2 = "Phoenix Suns"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)

    # team_name1 = "Miami Heat"
    # team_name2 = "Utah Jazz"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    # print(team1_name, team1_score, team2_name, team2_score)

    # team_name1 = "Miami Heat"
    # team_name2 = "Utah Jazz"

    # # Call predict_game function
    # team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games)
    # print(team1_name, team1_score, team2_name, team2_score)

    team_name1 = "Toronto Raptors"
    team_name2 = "Cleveland Cavaliers"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 1)
    print(team1_name, team1_score, team2_name, team2_score)
    
    team_name1 = "Toronto Raptors"
    team_name2 = "Cleveland Cavaliers"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    print(team1_name, team1_score, team2_name, team2_score)

    team_name2 = "Toronto Raptors"
    team_name1 = "Cleveland Cavaliers"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 1)
    print(team1_name, team1_score, team2_name, team2_score)

    team_name2 = "Toronto Raptors"
    team_name1 = "Cleveland Cavaliers"

    # Call predict_game function
    team1_name, team1_score, team2_name, team2_score = predict_winner(team_name1, team_name2, model, db, num_games, 0)
    print(team1_name, team1_score, team2_name, team2_score)

if __name__ == "__main__":
    test_predict_game()

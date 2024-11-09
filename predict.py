from nba_api.stats.static import teams
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def predict_winner(first_team, second_team):
    matching_teams1 = teams.find_teams_by_full_name(first_team)
    matching_teams2 = teams.find_teams_by_full_name(second_team)
    error_message = "Team not found"

    # Check first team
    if not matching_teams1:
        print(error_message, first_team)
        return error_message, None

    # Check second team
    if not matching_teams2:
        print(error_message, second_team)
        return error_message, None
        
    # Both teams found, get their info
    team_info1 = matching_teams1[0]  # Get the first match
    team_id1 = team_info1['id']
    team_name1 = team_info1['full_name']
    
    team_info2 = matching_teams2[0]  # Get the first match
    team_id2 = team_info2['id']
    team_name2 = team_info2['full_name']
    
    # Connect to MongoDB and query team scores
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client['basketball_data']
    collection = db['teams']
    
    # Find scores for both teams
    team1_data = collection.find_one({'TEAM_ID': team_id1})
    team2_data = collection.find_one({'TEAM_ID': team_id2})
    
    team1_score = team1_data['SCORE'] if team1_data else None
    team2_score = team2_data['SCORE'] if team2_data else None
            
    # Compare scores and return winner/loser
    if team1_score > team2_score:
        return team_name1, team_name2
    else:
        return team_name2, team_name1
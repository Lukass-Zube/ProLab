from pymongo import MongoClient
from nba_api.stats.endpoints import leaguedashteamstats
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['teams']

def calculate_master_rank(teams):
    for team in teams:
        # Sum the ranks to get a combined rank
        team['combined_rank'] = sum([
            team.get('AST_RANK', 0),
            team.get('BLK_RANK', 0),
            team.get('DREB_RANK', 0),
            team.get('FG3A_RANK', 0),
            team.get('FG3M_RANK', 0),
            team.get('FG_PCT_RANK', 0),
            team.get('FTA_RANK', 0),
            team.get('FTM_RANK', 0),
            team.get('GP_RANK', 0),
            team.get('L_RANK', 0),
            team.get('MIN_RANK', 0),
            team.get('OREB_RANK', 0),
            team.get('PF_RANK', 0),
            team.get('PLUS_MINUS_RANK', 0),
            team.get('PTS_RANK', 0),
            team.get('REB_RANK', 0),
            team.get('STL_RANK', 0),
            team.get('TOV_RANK', 0),
            team.get('W_RANK', 0),
        ])
    
    # Sort teams based on combined rank
    teams.sort(key=lambda x: x['combined_rank'])
    
    # Assign master rank based on sorted order
    for index, team in enumerate(teams):
        team['master_rank'] = index + 1  # Rank starts from 1

# Fetch all teams from the database
teams_stats = list(collection.find({}))

# Calculate master ranks
calculate_master_rank(teams_stats)

# Update the database with the master rank
for team in teams_stats:
    collection.update_one(
        {'TEAM_ID': team['TEAM_ID']},  # Match the team by TEAM_ID
        {'$set': {'MASTER_RANK': team['master_rank']}}  # Update the master_rank
    )

# Print teams with their master ranks (optional)
for team in teams_stats:
    print(f"{team['TEAM_NAME']} - Master Rank: {team['master_rank']}")
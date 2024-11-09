from pymongo import MongoClient
from nba_api.stats.endpoints import leaguedashteamstats
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['teams']

# Fetch the team stats for the season
team_stats = leaguedashteamstats.LeagueDashTeamStats(season='2024-25')
stats_df = team_stats.get_data_frames()[0]

# Define positive (good) and negative (bad) attributes based on available stats
positive_attributes = ['W_PCT', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'PFD', 'PTS', 'PLUS_MINUS']
negative_attributes = ['TOV', 'PF', 'BLKA']  # Including "BLKA" as a "bad" attribute

# Prepare the JSON structure
teams_scores = []
for _, row in stats_df.iterrows():
    # Calculate the score as sum of good attributes - sum of bad attributes
    team_score = sum(row[attr] for attr in positive_attributes) - sum(row[attr] for attr in negative_attributes)
    team_data = {
        "TEAM_NAME": row['TEAM_NAME'],
        "TEAM_ID": row['TEAM_ID'],
        "SCORE": team_score
    }
    teams_scores.append(team_data)

# Connect to MongoDB and insert/update team scores

# Insert or update each team's data
for team in teams_scores:
    collection.insert_one(team)

print("Team scores updated in MongoDB database")

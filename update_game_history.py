from nba_api.stats.endpoints import leaguegamefinder
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['games']

# Find the latest game date in the database
latest_game = collection.find_one(sort=[("GAME_DATE", -1)])
latest_game_date = latest_game['GAME_DATE'] if latest_game else None

# Initialize LeagueGameFinder with a start date if there's a latest game date
if latest_game_date:
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2024-25', date_from_nullable=latest_game_date)
else:
    gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable='2024-25')

# Retrieve the data as a DataFrame
games_df = gamefinder.get_data_frames()[0]

# Convert all game data to dictionary format
game_data = games_df.to_dict('records')

# Check for existing games in the database
existing_game_ids = set(doc['GAME_ID'] for doc in collection.find({}, {'GAME_ID': 1}))

# Filter out games that are already in the database
new_game_data = [game for game in game_data if game['GAME_ID'] not in existing_game_ids]

# Insert new documents
if new_game_data:
    collection.insert_many(new_game_data)
    print(f"{len(new_game_data)} new games added to the database.")
else:
    print("No new games to add.")
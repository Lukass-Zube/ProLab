from nba_api.stats.endpoints import leaguegamefinder
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time
import requests
from nba_api.stats.library.http import NBAStatsHTTP
from datetime import datetime

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['games']

def get_game_data(latest_game_date=None):
    try:
        # Add a delay to avoid rate limiting
        time.sleep(2)
        
        # Format the date properly if it exists
        if latest_game_date:
            try:
                # Convert the date string to datetime object and format it
                date_obj = datetime.strptime(str(latest_game_date), '%Y-%m-%d')
                formatted_date = date_obj.strftime('%m/%d/%Y')
                print(f"Formatted date: {formatted_date}")
            except Exception as e:
                print(f"Date formatting error: {e}")
                formatted_date = None
        else:
            formatted_date = None
        
        print(f"Attempting to fetch games. Latest game date: {formatted_date}")
        
        # Initialize LeagueGameFinder with custom headers
        headers = {
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Connection': 'keep-alive',
            'Referer': 'https://stats.nba.com/',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        # Try without date first to test connection
        print("Testing API connection without date filter...")
        gamefinder = leaguegamefinder.LeagueGameFinder(
            season_nullable='2024-25',
            headers=headers,
            timeout=60
        )
        
        # If basic connection works, then try with date
        if formatted_date:
            print(f"Fetching games from date: {formatted_date}")
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable='2024-25',
                date_from_nullable=formatted_date,
                headers=headers,
                timeout=60
            )
        
        # Try to get the raw response before processing
        try:
            raw_response = gamefinder.nba_response._response
            if not raw_response:
                print("Warning: Empty response received from API")
                return None
            print(f"Raw API Response length: {len(raw_response)}")
            print(f"Raw API Response preview: {raw_response[:500]}...")
        except Exception as e:
            print(f"Error accessing raw response: {str(e)}")
            return None
        
        # Get the data frames
        games_df = gamefinder.get_data_frames()[0]
        return games_df
        
    except Exception as e:
        print(f"General Exception: {str(e)}")
        print(f"Exception type: {type(e)}")
        return None

# Main execution
try:
    # Find the latest game date in the database
    latest_game = collection.find_one(sort=[("GAME_DATE", -1)])
    latest_game_date = latest_game['GAME_DATE'] if latest_game else None
    print("Latest game date:", latest_game_date)
    
    # Get the game data
    games_df = get_game_data(latest_game_date)
    
    if games_df is not None and not games_df.empty:
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
    else:
        print("Failed to retrieve game data")

except Exception as e:
    print(f"Error in main execution: {str(e)}")
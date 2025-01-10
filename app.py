from datetime import datetime, timezone
import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from helper.update_time import get_last_update_time, set_last_update_time
from predict import predict_winner
from helper.custom_errors import TeamNotFoundError
import subprocess
import joblib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

model = joblib.load('basketball_prediction_model.joblib')
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']

@app.route('/')
def home():
    teams_collection = db['teams']
    teams = list(teams_collection.find({}, {'TEAM_NAME': 1}))  # Fetch team names
    return render_template('form.html', teams=teams)

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'GET':
        return redirect(url_for('home'))

    current_time_utc = datetime.now(timezone.utc)  # Get the current UTC time
    last_update_time = get_last_update_time(db)

    if last_update_time.tzinfo is None:
        last_update_time = last_update_time.replace(tzinfo=timezone.utc)

    # Check if the last update was more than an hour ago
    if (current_time_utc - last_update_time).total_seconds() > 3600:  # 3600 seconds = 1 hour
        subprocess.run(['python', 'nba_api_call/update_game_history.py'])
        subprocess.run(['python', 'nba_api_call/update_team_score.py'])
        subprocess.run(['python', 'nba_api_call/create_rank.py'])
        set_last_update_time(current_time_utc, db)
    
    first_team = request.form.get('first_team')
    second_team = request.form.get('second_team')
    num_games = request.form.get('historical_game_number')
    
    error_message = None
    if not first_team or not second_team or not num_games:
        error_message = "One or more fields haven't been selected"

    if error_message:
        teams_collection = db['teams']
        teams = list(teams_collection.find({}, {'TEAM_NAME': 1}))  
        return render_template('form.html', teams=teams, error_message=error_message)

    try:
        num_games = int(num_games)
        first_team, first_team_score, second_team, second_team_score = predict_winner(first_team, second_team, model, db, num_games)
    


        games_collection = db['games']
        first_team_abbreviation = games_collection.find_one({'TEAM_NAME': first_team})['TEAM_ABBREVIATION']
        second_team_abbreviation = games_collection.find_one({'TEAM_NAME': second_team})['TEAM_ABBREVIATION']

        last_games = list(games_collection.find({
            'MATCHUP': {'$regex': f"({first_team_abbreviation}.*[@|vs.]\\s*{second_team_abbreviation})|({second_team_abbreviation}.*[@|vs.]\\s*{first_team_abbreviation})"}
        }).sort('GAME_DATE', -1).limit(10))
        
        consolidated_games = []
        seen_game_ids = set()
        for game in last_games:
            if game['GAME_ID'] not in seen_game_ids:
                # Find the opponent's record
                opponent_game = next(
                    (g for g in last_games if g['GAME_ID'] == game['GAME_ID'] and g != game), None
                )
                if opponent_game:
                    consolidated_games.append({
                        'date': game['GAME_DATE'],
                        'team1': game['TEAM_NAME'],
                        'team1_score': game['PTS'],
                        'team1_result': game['WL'],
                        'team2': opponent_game['TEAM_NAME'],
                        'team2_score': opponent_game['PTS'],
                        'team2_result': opponent_game['WL']
                    })
                    seen_game_ids.add(game['GAME_ID'])

            # Stop when we have 5 games
            if len(consolidated_games) == 5:
                break

        print("Last Games:", consolidated_games)
        

    except TeamNotFoundError as e:
        return render_template('prediction.html', error_message=str(e)) #sis principa nekad nenostrada
    
    if first_team_score > second_team_score:
        wining_team = first_team
        losing_team = second_team
        wining_team_score = first_team_score
        losing_team_score = second_team_score
    else:
        wining_team = second_team
        losing_team = first_team
        wining_team_score = second_team_score
        losing_team_score = first_team_score
    
    return render_template(
        'prediction.html', 
        wining_team=wining_team, 
        wining_team_score=wining_team_score, 
        losing_team=losing_team, 
        losing_team_score=losing_team_score,
        last_games=consolidated_games)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
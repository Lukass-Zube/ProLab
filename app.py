from datetime import datetime, timezone
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
from helper.update_time import get_last_update_time, set_last_update_time
from predict_2_team import predict_winner
from helper.custom_errors import TeamNotFoundError
import subprocess
import joblib
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

bcrypt = Bcrypt(app)

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
user_db = client['user_data']
saved_predictions = client['saved_predictions']
users_collection = user_db['users']

# Example of adding a new user (registration)
def add_user(username, password):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({'username': username, 'password': hashed_password})

# Example of checking user credentials (login)
def check_user(username, password):
    user = users_collection.find_one({'username': username})
    if user and bcrypt.check_password_hash(user['password'], password):
        return True
    return False

class User(UserMixin):
    def __init__(self, username):
        self.id = username

# Set up the unauthorized handler to flash a message
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('You need to log in to access this page.')
    return redirect('/')

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({'username': user_id})
    if user:
        return User(user_id)
    return None

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Both username and password are required.'
        })

    user = users_collection.find_one({'username': username})
    if user and bcrypt.check_password_hash(user['password'], password):
        login_user(User(username))
        return jsonify({
            'success': True,
            'redirect': url_for('home')
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        })

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']

    if users_collection.find_one({'username': username}):
        flash('Username already exists. Please choose a different one.')
        return redirect(url_for('home'))  # Reload the page with the signup modal

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({'username': username, 'password': hashed_password})
    flash('Account created successfully! Please log in.')
    return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))

model = joblib.load('basketball_prediction_model_2_team.joblib')
db = client['basketball_data']

@app.route('/')
def home():
    teams_collection = db['teams']
    teams = list(teams_collection.find({}, {'TEAM_NAME': 1}))  # Fetch team names
    return render_template('form.html', teams=teams, is_logged_in=current_user.is_authenticated)

@app.route('/prediction', methods=['GET', 'POST'])
@login_required
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
               
                opponent_game = next(
                    (g for g in last_games if g['GAME_ID'] == game['GAME_ID'] and g != game), None
                )
                if opponent_game:
                    if game['TEAM_NAME'] > opponent_game['TEAM_NAME']:
                        team1, team1_score, team1_result = opponent_game['TEAM_NAME'], opponent_game['PTS'], opponent_game['WL']
                        team2, team2_score, team2_result = game['TEAM_NAME'], game['PTS'], game['WL']
                        
                        team1_stats = {key: opponent_game[key] for key in [
                           'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
                           'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB',
                           'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS'
                        ]}
                        team2_stats = {key: game[key] for key in [
                           'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
                           'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB',
                           'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS'
                        ]}
                    else:
                        team1, team1_score, team1_result = game['TEAM_NAME'], game['PTS'], game['WL']
                        team2, team2_score, team2_result = opponent_game['TEAM_NAME'], opponent_game['PTS'], opponent_game['WL']

                        team1_stats = {key: game[key] for key in [
                           'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
                           'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB',
                           'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS'
                        ]}
                        team2_stats = {key: opponent_game[key] for key in [
                           'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT',
                           'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB',
                           'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS'
                        ]}

                consolidated_games.append({
                    'date': game['GAME_DATE'],
                    'team1': team1,
                    'team1_score': team1_score,
                    'team1_result': team1_result,
                    'team1_stats': team1_stats,
                    'team2': team2,
                    'team2_score': team2_score,
                    'team2_result': team2_result,
                    'team2_stats': team2_stats
                    })
                seen_game_ids.add(game['GAME_ID'])

        consolidated_games = consolidated_games[:5]
        # Sort consolidated_games by date in ascending order
        consolidated_games.sort(key=lambda x: x['date'], reverse=True)
    
    except TeamNotFoundError as e:
        return render_template('prediction.html', error_message=str(e)) #sis principa nekad nenostrada

    if first_team < second_team:  # Alphabetical ordering
        team1, team1_score = first_team, first_team_score
        team2, team2_score = second_team, second_team_score
    else:
        team1, team1_score = second_team, second_team_score
        team2, team2_score = first_team, first_team_score

    #  Pass team1 and team2 to the template, and determine the winner/loser dynamically
    return render_template(
        'prediction.html',
        team1=team1,
        team1_score=team1_score,
        team2=team2,
        team2_score=team2_score,
        last_games=consolidated_games,
        game_count=num_games
    )

@app.route('/save_prediction', methods=['POST'])
@login_required
def save_prediction():
    # Check for existing prediction with same teams and scores
    existing_prediction = db['saved_predictions'].find_one({
        'user_id': current_user.id,
        'team1': request.form['team1'],
        'team1_score': float(request.form['team1_score']),
        'team2': request.form['team2'],
        'team2_score': float(request.form['team2_score']),
        'game_count': int(request.form['game_count'])
    })
    
    if existing_prediction:
        return jsonify({
            'success': False,
            'message': 'You have already saved this prediction!'
        })
    
    prediction_data = {
        'user_id': current_user.id,
        'team1': request.form['team1'],
        'team1_score': float(request.form['team1_score']),
        'team2': request.form['team2'],
        'team2_score': float(request.form['team2_score']),
        'game_count': int(request.form['game_count']),
        'date_saved': datetime.now(timezone.utc)
    }
    print(prediction_data)
    # Save to MongoDB
    saved_predictions['saved_predictions'].insert_one(prediction_data)
    
    return jsonify({
        'success': True,
        'message': 'Prediction saved successfully!'
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
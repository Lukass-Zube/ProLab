from datetime import datetime, timezone
import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from update_time import get_last_update_time, set_last_update_time
from predict import predict_winner
from custom_errors import TeamNotFoundError
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
    return render_template('form.html')

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
        subprocess.run(['python', 'update_game_history.py'])
        set_last_update_time(current_time_utc, db)
    
    first_team = request.form.get('first_team')
    second_team = request.form.get('second_team')
    
    try:
        first_team, first_team_score, second_team, second_team_score = predict_winner(first_team, second_team, model, db)
    except TeamNotFoundError as e:
        return render_template('prediction.html', error_message=str(e))
    
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
    
    return render_template('prediction.html', wining_team=wining_team, wining_team_score=wining_team_score, losing_team=losing_team, losing_team_score=losing_team_score)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
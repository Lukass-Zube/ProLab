from flask import Flask, render_template, request, redirect, url_for
from predict import predict_winner
from custom_errors import TeamNotFoundError
import subprocess
import joblib
import time


app = Flask(__name__)

model = joblib.load('basketball_prediction_model.joblib')
last_update_time = 0  # Initialize last update time
update_interval = 3600

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    global last_update_time

    if request.method == 'GET':
        return redirect(url_for('home'))
    
    # Update team scores before making prediction
    current_time = time.time()
    if current_time - last_update_time >= update_interval:
        subprocess.run(['python', 'update_game_history.py'])
        last_update_time = current_time  # Update the last run time
    
    first_team = request.form.get('first_team')
    second_team = request.form.get('second_team')
    
    try:
        first_team, first_team_score, second_team, second_team_score = predict_winner(first_team, second_team, model)
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
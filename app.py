from flask import Flask, render_template, request, redirect, url_for
from predict import predict_winner
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'GET':
        return redirect(url_for('home'))
    # Update team scores before making prediction
    subprocess.run(['python', 'update_team_score.py'])
    
    first_team = request.form.get('first_team')
    second_team = request.form.get('second_team')
    wining_team, losing_team, prob = predict_winner(first_team, second_team)
    if wining_team == "Team not found":
        return render_template('prediction.html', error_message=wining_team)
    return render_template('prediction.html', wining_team=wining_team, losing_team=losing_team, prob=f"{prob*100:.2f}%")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
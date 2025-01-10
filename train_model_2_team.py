from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import os
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, r2_score, root_mean_squared_error
import joblib
from scipy.stats import randint

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['games']

# Modified query to get paired team data
pipeline = [
    {
        '$sort': {'GAME_DATE': 1}
    },
    {
        '$group': {
            '_id': '$GAME_ID',
            'team1_stats': {'$first': '$$ROOT'},
            'team2_stats': {'$last': '$$ROOT'}
        }
    },
    {
        '$limit': collection.count_documents({}) // 2 - 50  # Divide by 2 since we're grouping pairs
    }
]

query_result = list(collection.aggregate(pipeline))

# Process the paired data into a flat structure
processed_data = []
for game in query_result:
    # Calculate home advantage based on MATCHUP
    team1_matchup = game['team1_stats']['MATCHUP']
    team2_matchup = game['team2_stats']['MATCHUP']
    
    # '@' in matchup means away game, 'vs.' means home game
    team1_home = 1 if 'vs.' in team1_matchup else 0
    team2_home = 1 if 'vs.' in team2_matchup else 0
    
    game_data = {
        'GAME_ID': game['_id'],
        
        # Team 2 features
        'TEAM1_ID': game['team1_stats']['TEAM_ID'],
        'TEAM1_HOME_ADVANTAGE': team1_home,
        'TEAM1_PTS': game['team1_stats']['PTS'],
        'TEAM1_MIN': game['team1_stats']['MIN'],
        'TEAM1_FGM': game['team1_stats']['FGM'],
        'TEAM1_FGA': game['team1_stats']['FGA'],
        'TEAM1_FG_PCT': game['team1_stats']['FG_PCT'],
        'TEAM1_FG3M': game['team1_stats']['FG3M'],
        'TEAM1_FG3A': game['team1_stats']['FG3A'],
        'TEAM1_FG3_PCT': game['team1_stats']['FG3_PCT'],
        'TEAM1_FTM': game['team1_stats']['FTM'],
        'TEAM1_FTA': game['team1_stats']['FTA'],
        'TEAM1_FT_PCT': game['team1_stats']['FT_PCT'],
        'TEAM1_OREB': game['team1_stats']['OREB'],
        'TEAM1_DREB': game['team1_stats']['DREB'],
        'TEAM1_REB': game['team1_stats']['REB'],
        'TEAM1_AST': game['team1_stats']['AST'],
        'TEAM1_STL': game['team1_stats']['STL'],
        'TEAM1_BLK': game['team1_stats']['BLK'],
        'TEAM1_TOV': game['team1_stats']['TOV'],
        'TEAM1_PF': game['team1_stats']['PF'],
        'TEAM1_PLUS_MINUS': game['team1_stats']['PLUS_MINUS'],
        
        # Team 2 features
        'TEAM2_ID': game['team2_stats']['TEAM_ID'],
        'TEAM2_HOME_ADVANTAGE': team2_home,
        'TEAM2_PTS': game['team2_stats']['PTS'],
        'TEAM2_MIN': game['team2_stats']['MIN'],
        'TEAM2_FGM': game['team2_stats']['FGM'],
        'TEAM2_FGA': game['team2_stats']['FGA'],
        'TEAM2_FG_PCT': game['team2_stats']['FG_PCT'],
        'TEAM2_FG3M': game['team2_stats']['FG3M'],
        'TEAM2_FG3A': game['team2_stats']['FG3A'],
        'TEAM2_FG3_PCT': game['team2_stats']['FG3_PCT'],
        'TEAM2_FTM': game['team2_stats']['FTM'],
        'TEAM2_FTA': game['team2_stats']['FTA'],
        'TEAM2_FT_PCT': game['team2_stats']['FT_PCT'],
        'TEAM2_OREB': game['team2_stats']['OREB'],
        'TEAM2_DREB': game['team2_stats']['DREB'],
        'TEAM2_REB': game['team2_stats']['REB'],
        'TEAM2_AST': game['team2_stats']['AST'],
        'TEAM2_STL': game['team2_stats']['STL'],
        'TEAM2_BLK': game['team2_stats']['BLK'],
        'TEAM2_TOV': game['team2_stats']['TOV'],
        'TEAM2_PF': game['team2_stats']['PF'],
        'TEAM2_PLUS_MINUS': game['team2_stats']['PLUS_MINUS'],
    }
    processed_data.append(game_data)

# Convert to DataFrame
df = pd.DataFrame(processed_data)

# Drop the _id column if it exists
if '_id' in df.columns:
    df = df.drop(columns=['_id'])

# Drop rows with missing values
df.dropna(inplace=True)

# Split the data into features (X) and target (y)
X = df.drop(columns=['TEAM1_PTS', 'TEAM2_PTS', 'GAME_ID'])
y = df[['TEAM1_PTS', 'TEAM2_PTS']]

# Define categorical and numerical columns
categorical_features = ['TEAM1_ID', 'TEAM2_ID', 'TEAM1_HOME_ADVANTAGE', 'TEAM2_HOME_ADVANTAGE']
numerical_features = [col for col in X.columns if col not in categorical_features]

# Create the preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ('categorical', OneHotEncoder(handle_unknown='ignore'), categorical_features),
        ('numerical', 'passthrough', numerical_features)
    ]
)

# Create a pipeline with preprocessing and model
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('model', MultiOutputRegressor(
        GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=10,
            subsample=0.8,
            min_samples_split=5,
            min_samples_leaf=3,
            random_state=42,
            verbose=1,
            tol=1e-4,
            n_iter_no_change=10
        ),
        n_jobs=-1
    ))
])

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

# Train the model
pipeline.fit(X_train, y_train)

# Make predictions and evaluate
y_pred = pipeline.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse:.2f}")
print(f"Root Mean Squared Error: {rmse:.2f}")
print(f"R² Score: {r2:.2f}")

# Save the model
joblib.dump(pipeline, 'basketball_prediction_model_2_team.joblib')
print("\nModel saved as 'basketball_prediction_model_2_team.joblib'")

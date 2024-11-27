from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['games']

# Query the data from MongoDB
query = list(collection.find({}, {
    "TEAM_ID": 1,
    "MIN": 1,
    "PTS": 1,
    "FGM": 1,
    "FGA": 1,
    "FG_PCT": 1,
    "FG3M": 1,
    "FG3A": 1,
    "FG3_PCT": 1,
    "FTM": 1,
    "FTA": 1,
    "FT_PCT": 1,
    "OREB": 1,
    "DREB": 1,
    "REB": 1,
    "AST": 1,
    "STL": 1,
    "BLK": 1,
    "TOV": 1,
    "PF": 1,
    "PLUS_MINUS": 1
}))

# Convert the data to a DataFrame
df = pd.DataFrame(query)

# Drop the _id column if it exists
if '_id' in df.columns:
    df = df.drop(columns=['_id'])

# Drop rows with missing values
df.dropna(inplace=True)

# Split the data into features (X) and target (y)
X = df.drop(columns=['PTS'])
y = df['PTS']

# Define the column transformer for one-hot encoding
preprocessor = ColumnTransformer(
    transformers=[
        ('team_id', OneHotEncoder(handle_unknown='ignore'), ['TEAM_ID']),
    ],
    remainder='passthrough'  # Keep other columns as they are
)

# Create a pipeline with preprocessing and model
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42))
])

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
pipeline.fit(X_train, y_train)

# Make predictions on the test set
y_pred = pipeline.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse:.2f}")
print(f"Root Mean Squared Error: {rmse:.2f}")
print(f"R² Score: {r2:.2f}")

# Save the model using Joblib
joblib.dump(pipeline, 'basketball_prediction_model.joblib')
print("\nModel saved as 'basketball_prediction_model.joblib'")

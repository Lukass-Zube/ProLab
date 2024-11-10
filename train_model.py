from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['basketball_data']
collection = db['games']

# Query the data from MongoDB
query = list(collection.find({}, {
    "PLUS_MINUS": 1,
    "PTS": 1,
    "FG_PCT": 1,
    "FGM": 1,
    "FG3_PCT": 1,
    "DREB": 1,
    "FG3M": 1,
    "WL": 1  # Outcome field, currently "W" or "L"
}))

# Convert the data to a DataFrame
df = pd.DataFrame(query)

# Drop the _id column if it exists
if '_id' in df.columns:
    df = df.drop(columns=['_id'])
# Convert the WL field to a numeric outcome
df['outcome'] = df['WL'].apply(lambda x: 1 if x == 'W' else 0)
df.drop(columns=['WL'], inplace=True)

# Drop rows with any missing values (optional)
df.dropna(inplace=True)

# Split the data into features (X) and target (y)
X = df.drop(columns=['outcome'])
y = df['outcome']

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the logistic regression model
model = LogisticRegression()
model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = model.predict(X_test)

print(X_test)
# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print("Model Accuracy:", accuracy)
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save the model using Joblib
joblib.dump(model, 'basketball_prediction_model.joblib')
print("Model saved as 'basketball_prediction_model.joblib'")

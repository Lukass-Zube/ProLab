from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_last_update_time(db):
    collection = db['settings']
    doc = collection.find_one({'_id': 'last_update_time'})
    if doc is None:
        return 0  # Default to 0 if not set
    return doc['last_update_time']

def set_last_update_time(current_time, db):
    collection = db['settings']
    collection.update_one(
        {'_id': 'last_update_time'},
        {'$set': {'last_update_time': current_time}},
        upsert=True
    )
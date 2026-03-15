# src/api/db.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(".env.local")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB", "Fitapp")

try:
    # Production-hardened connection settings
    client = MongoClient(
        MONGODB_URI, 
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=20000,
        socketTimeoutMS=20000,
        heartbeatFrequencyMS=10000,
        maxPoolSize=10,
        retryWrites=True
    )
    db     = client[MONGODB_DB]
    workouts_col         = db["workouts"]
    validation_cache_col = db["validation_cache"]
    
    # Force a check to see if we can actually reach the server
    client.admin.command('ping')
    
    # Indexes (no-op if already exist)
    workouts_col.create_index([("workout_id", 1), ("user_id", 1)], unique=True)
    validation_cache_col.create_index("cache_key", unique=True)
    print(f"✓ MongoDB connected: {MONGODB_DB}")
except Exception as e:
    print(f"⚠️ MongoDB Warning (Continuing in Offline Mode): {e}")
    # Application continues but these will be None
    workouts_col = None
    validation_cache_col = None
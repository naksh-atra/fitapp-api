# src/api/db.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(".env.local")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB")

client = MongoClient(MONGODB_URI)
db     = client[MONGODB_DB]
workouts_col         = db["workouts"]
validation_cache_col = db["validation_cache"]

# Indexes (safe to run every startup — no-op if already exist)
workouts_col.create_index([("workout_id", 1), ("user_id", 1)], unique=True)
validation_cache_col.create_index("cache_key", unique=True)

print(f"\nMongoDB connected: {MONGODB_DB}\n")
# src/api/db.py
import os
import ssl
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(".env.local")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB", "Fitapp")

workouts_col = None
validation_cache_col = None

try:
    kwargs = dict(
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        heartbeatFrequencyMS=10000,
        maxPoolSize=10,
        retryWrites=True,
    )

    if "mongodb+srv" in MONGODB_URI:
        kwargs["tls"] = True
        kwargs["tlsAllowInvalidCertificates"] = True
        kwargs["tlsAllowInvalidHostnames"] = True
        kwargs["ssl_cert_reqs"] = ssl.CERT_NONE

    client = MongoClient(MONGODB_URI, **kwargs)
    client.admin.command('ping')

    db = client[MONGODB_DB]
    workouts_col = db["workouts"]
    validation_cache_col = db["validation_cache"]

    workouts_col.create_index([("workout_id", 1), ("user_id", 1)], unique=True)
    validation_cache_col.create_index("cache_key", unique=True)
    print("(i) MongoDB connected: " + MONGODB_DB)
except Exception as e:
    print("(i) MongoDB unavailable - continuing in offline mode")

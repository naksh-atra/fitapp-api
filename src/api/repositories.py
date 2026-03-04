from datetime import datetime
from typing import Dict, Optional
from db import workouts_col, validation_cache_col


def save_workout(user_id: str, workout_id: str, request_payload: Dict, data: Dict) -> None:
    now = datetime.utcnow().isoformat()
    doc = {
        "workout_id":      workout_id,
        "user_id":         user_id,
        "request_payload": request_payload,
        "data":            data,
        "updated_at":      now,
    }
    workouts_col.update_one(
        {"workout_id": workout_id, "user_id": user_id},
        {"$setOnInsert": {"created_at": now}, "$set": doc},
        upsert=True,
    )


def get_workout(user_id: str, workout_id: str) -> Optional[Dict]:
    doc = workouts_col.find_one({"workout_id": workout_id, "user_id": user_id})
    return doc["data"] if doc else None


def get_cached_validation(cache_key: str) -> Optional[Dict]:
    doc = validation_cache_col.find_one({"cache_key": cache_key})
    return doc["validation_result"] if doc else None


def save_cached_validation(cache_key: str, meta: Dict, validation_result: Dict) -> None:
    now = datetime.utcnow().isoformat()
    validation_cache_col.update_one(
        {"cache_key": cache_key},
        {
            "$setOnInsert": {"created_at": now},
            "$set": {
                "cache_key":         cache_key,
                "validation_result": validation_result,
                **meta,
            }
        },
        upsert=True,
    )

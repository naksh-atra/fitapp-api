"""
db_models.py
Pydantic models for MongoDB documents.
These define the shape of data written to and read from MongoDB.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import json


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

def utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
# workouts collection
# ---------------------------------------------------------------------------

class ExerciseDocument(BaseModel):
    """Single exercise inside a workout"""
    name:         str
    type:         str                        # compound / accessory / isolation
    sets:         List[int]                  # [3, 5]
    reps:         List[int]                  # [6, 10]
    rest_seconds: List[int]                  # [90, 180]
    rpe:          str                        # "7-9"
    tempo:        Optional[str] = None       # "3010"
    notes:        Optional[str] = None


class ModificationRecord(BaseModel):
    """Embedded in workouts.modifications[] — one swap per entry"""
    original_exercise:    str
    replacement_exercise: str
    reason:               str
    verdict:              str               # GREEN / YELLOW / RED
    reasoning:            str
    citations:            List[str] = []
    modified_at:          str = Field(default_factory=utcnow)


class WorkoutData(BaseModel):
    """The data block inside a workout document — mirrors what your API returns"""
    exercises:        List[Dict[str, Any]]   # raw exercise dicts from generator
    citations:        List[str]
    evidence_level:   str                   # HIGH / MEDIUM / LOW / UNKNOWN
    equipment:        str
    goal:             str
    validation_source: Optional[str] = None  # perplexity_api / perplexity_error / cache


class WorkoutDocument(BaseModel):
    """
    Represents one document in the workouts collection.

    workouts_col.insert_one(WorkoutDocument(...).to_mongo())
    """
    workout_id:   str
    user_id:      str = "anonymous"          # replaced with real id when JWT lands
    goal:         str
    equipment:    str
    experience:   str
    week:         int
    data:         WorkoutData
    modifications: List[ModificationRecord] = []
    created_at:   str = Field(default_factory=utcnow)
    updated_at:   str = Field(default_factory=utcnow)

    def to_mongo(self) -> dict:
        """Convert to plain dict suitable for pymongo insert"""
        return self.model_dump()


# ---------------------------------------------------------------------------
# validation_cache collection
# ---------------------------------------------------------------------------

class ValidationResult(BaseModel):
    """
    Mirrors the dict returned by PrescriptionValidator.validate_prescription().
    Store this inside ValidationCacheDocument.validation_result.
    """
    validated:        bool
    goal:             str
    evidence_summary: str
    citations:        List[str]
    confidence:       str                  # high / medium / low / unknown
    validated_at:     str
    source:           str                  # perplexity_api / perplexity_error / etc.


class ValidationCacheDocument(BaseModel):
    """
    Represents one document in the validation_cache collection.

    validation_cache_col.update_one(
        {"cache_key": doc.cache_key},
        {"$set": doc.to_mongo()},
        upsert=True
    )
    """
    cache_key:         str
    goal:              str
    equipment:         str
    experience:        str
    prescription_hash: str                 # hash of exercise names, for cache invalidation
    validation_result: ValidationResult
    created_at:        str = Field(default_factory=utcnow)

    @staticmethod
    def make_prescription_hash(exercises: List[Dict]) -> str:
        """Stable hash of exercise list so cache is prescription-specific"""
        names = sorted([ex.get("name", "") for ex in exercises])
        return hashlib.md5(json.dumps(names).encode()).hexdigest()

    def to_mongo(self) -> dict:
        return self.model_dump()


# ---------------------------------------------------------------------------
# users collection (placeholder for JWT milestone)
# ---------------------------------------------------------------------------

class UserDocument(BaseModel):
    """
    Represents one document in the users collection.
    Not used until JWT milestone.
    """
    user_id:         str
    email:           str
    hashed_password: str
    created_at:      str = Field(default_factory=utcnow)
    last_seen_at:    str = Field(default_factory=utcnow)

    def to_mongo(self) -> dict:
        return self.model_dump()

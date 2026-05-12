"""
FitApp Workout Generator API v2.0
Science-based weekly plans powered by YAML research prescriptions.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import traceback
from dotenv import load_dotenv
from enum import Enum

# Add src to Python path before any other imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(
    dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env.local",
    override=True
)

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import uvicorn

from src.api.auth import get_current_user

try:
    from generator.workout_engine import WorkoutGenerator
    print("✓ WorkoutGenerator imported successfully")
except ImportError as e:
    print(f"import error: {e}")
    sys.exit(1)

try:
    from validation.research_validator import ResearchValidator
    from validation.validation_cache import ValidationCache
    from validation.prescription_validator import PrescriptionValidator
    print("✓ Validation system imported successfully")
except ImportError as e:
    print(f"Validation system not yet implemented: {e}")
    ResearchValidator     = None
    ValidationCache       = None
    PrescriptionValidator = None

from src.api.repositories import (
    save_workout, get_workout, list_workouts,
    get_cached_validation as db_get_cache,
    save_cached_validation as db_save_cache
)

app = FastAPI(
    title="Science Based Workout Generator API",
    description=(
        "Science-based weekly workout planner with research-validated prescriptions.\n\n"
        "4 goals: hypertrophy, strength, endurance, fatloss\n"
        "Returns a full Monday–Sunday weekly plan per request."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = WorkoutGenerator()

try:
    from generator.workout_modifier import WorkoutModifier
    print("✓ WorkoutModifier imported successfully")
    modifier = WorkoutModifier()
    print("✓ WorkoutModifier initialized")
except Exception as e:
    print(f"⚠ WorkoutModifier disabled: {e}")
    modifier = None

try:
    prescription_validator = PrescriptionValidator()
    print("✓ Prescription validator initialized")
except Exception as e:
    print(f"⚠ Prescription validator failed: {e}")
    prescription_validator = None

validator = ResearchValidator() if ResearchValidator else None
cache     = ValidationCache()   if ValidationCache   else None

workout_sessions: Dict = {}


# ---------------------------------------------------------------------------
# Enums & request models
# ---------------------------------------------------------------------------
class Goal(str, Enum):
    hypertrophy = "hypertrophy"
    strength    = "strength"
    endurance   = "endurance"
    fatloss     = "fatloss"

class Equipment(str, Enum):
    gym  = "gym"
    home = "home"

class Experience(str, Enum):
    beginner     = "beginner"
    intermediate = "intermediate"
    advanced     = "advanced"

class WorkoutRequest(BaseModel):
    goal:       Goal
    equipment:  Equipment  = Equipment.gym
    experience: Experience = Experience.intermediate

class ModificationRequest(BaseModel):
    workout_id:           str
    original_exercise:    str
    replacement_exercise: str
    reason:               str
    goal:                 Goal = Goal.hypertrophy

class ApplyModificationRequest(BaseModel):
    workout_id:           str
    modification_id:      str
    original_exercise:    str
    replacement_exercise: str
    verdict:              str
    reasoning:            str
    citations:            list
    adjustments:          Optional[Dict] = None

class ValidateSwapRequest(BaseModel):
    original_exercise:    str
    replacement_exercise: str
    reason:               str
    goal:                 Goal = Goal.hypertrophy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_verdict_emoji(verdict: str) -> str:
    return {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(verdict.lower(), "⚪")

def _flatten_exercises(workout: Dict) -> List[Dict]:
    """
    Collect every exercise across all days of the weekly_plan.
    Used for validation and for exercise-lookup in modify/apply flows.
    """
    exercises = []
    for day_data in workout.get("weekly_plan", {}).values():
        raw = day_data.get("exercises", [])
        for item in raw:
            # HIIT circuits and threshold circuits nest their exercises under 'stations'
            if "stations" in item:
                for station in item["stations"]:
                    # stations may be dicts with an 'exercise' key (string) or full dicts
                    if isinstance(station, dict) and "name" not in station and "exercise" in station:
                        exercises.append({"name": station["exercise"], **station})
                    else:
                        exercises.append(station)
            else:
                exercises.append(item)
    return exercises

def _find_exercise_in_plan(workout: Dict, exercise_name: str) -> bool:
    """Return True if exercise_name appears anywhere in the weekly plan."""
    name_lower = exercise_name.lower()
    for day_data in workout.get("weekly_plan", {}).values():
        for item in day_data.get("exercises", []):
            if item.get("name", "").lower() == name_lower:
                return True
            # check inside circuit stations
            for station in item.get("stations", []):
                station_name = (
                    station.get("name") or station.get("exercise") or ""
                )
                if station_name.lower() == name_lower:
                    return True
    return False


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "🎯 FitApp Workout Generator API v2.0 - LIVE ✅",
        "status": "healthy",
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals": list(generator.prescriptions.keys()),
        "features": {
            "weekly_plan_generation": "✅ Operational - full Monday–Sunday split per goal",
            "workout_modification":   "✅ Ready" if modifier else "⚠️ Manual only",
            "modification_validation":"✅ Operational" if validator else "⚠️ Not configured",
            "research_citations":     "✅ Included",
            "dietary_disclaimer":     "✅ Appended to all fat loss plans",
        },
        "splits": {
            "hypertrophy": "Push/Pull/Legs × 2 (6 days) - Schoenfeld et al. 2016",
            "strength":    "Daily Undulating Periodization (4 days) - Zourdos et al. 2016",
            "endurance":   "Polarized 80/20 (5 days) - Seiler 2010",
            "fatloss":     "HIIT × 3 + Steady-State × 2 (5 days) - Alkahtani et al. 2023",
        },
        "endpoints": {
            "generate_workout":      "POST /generate_workout",
            "validate_modification": "POST /validate_modification",
            "apply_modification":    "POST /apply_modification",
            "validate_swap":         "POST /validate_swap",
            "list_workouts":         "GET /workouts",
            "test_goal":             "GET /test/{goal}",
            "docs":                  "/docs",
            "health":                "/health",
        },
    }


# ---------------------------------------------------------------------------
# POST /generate_workout  - primary endpoint
# ---------------------------------------------------------------------------
@app.post("/generate_workout")
async def generate_workout(
    request: WorkoutRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Generate a full Monday–Sunday science-based weekly training plan.
    Returns data.weekly_plan keyed by day name.
    """
    try:
        # 1. Generate weekly plan
        workout = generator.generate_weekly_plan(
            goal=request.goal.value,
            equipment=request.equipment.value,
            experience=request.experience.value,
        )

        workout_id          = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workout["workout_id"] = workout_id

        # 2. Validate prescription - feed flattened exercise list to validator
        if prescription_validator:
            all_exercises = _flatten_exercises(workout)
            validation_result = prescription_validator.validate_prescription(
                goal=request.goal.value,
                exercises=all_exercises,
                equipment=request.equipment.value,
                experience=request.experience.value,
            )
            workout["research_validation"] = {
                "validated":        validation_result["validated"],
                "evidence_level":   validation_result["confidence"].upper(),
                "evidence_summary": validation_result["evidence_summary"],
                "citations":        validation_result["citations"],
                "validated_at":     validation_result["validated_at"],
            }
            workout["evidence_level"]      = validation_result["confidence"].upper()
            workout["citations"]           = validation_result["citations"]
            workout["prescription_source"] = f"Research-validated {request.goal.value} protocol (2023-2025)"
            workout["validation_source"]   = validation_result.get("source", "")

        # 3. Store in-memory session (for modify flow)
        workout_sessions[workout_id] = workout

        # 4. Persist to MongoDB
        save_workout(
            user_id=user_id,
            workout_id=workout_id,
            request_payload=request.dict(),
            data=workout,
        )

        return {
            "status":               "success",
            "message":              f"Research-validated {request.goal.value} weekly plan generated",
            "workout_id":           workout_id,
            "data":                 workout,
            "modification_enabled": modifier is not None,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Goal '{request.goal}' not found. Available: {list(generator.prescriptions.keys())}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


# ---------------------------------------------------------------------------
# POST /validate_modification
# ---------------------------------------------------------------------------
@app.post("/validate_modification")
async def validate_modification(request: ModificationRequest):
    if not validator:
        raise HTTPException(
            status_code=503,
            detail="Validation system not configured. Set PERPLEXITY_API_KEY environment variable."
        )

    if request.workout_id not in workout_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Workout ID '{request.workout_id}' not found. Generate a workout first."
        )

    # Check if the exercise exists anywhere in the weekly plan
    stored_workout = workout_sessions[request.workout_id]
    if not _find_exercise_in_plan(stored_workout, request.original_exercise):
        raise HTTPException(
            status_code=404,
            detail=f"Exercise '{request.original_exercise}' not found in any session of workout '{request.workout_id}'."
        )

    import hashlib
    components  = f"{request.original_exercise}|{request.replacement_exercise}|{request.reason}|{request.goal}".lower()
    m_cache_key = hashlib.md5(components.encode()).hexdigest()

    print(f"DEBUG: Validating {request.original_exercise} -> {request.replacement_exercise}")

    # MongoDB cache
    cached = db_get_cache(m_cache_key)
    # File cache fallback
    if not cached and cache:
        cached = cache.get_cached_validation(
            request.original_exercise, request.replacement_exercise,
            request.reason, request.goal
        )

    if cached:
        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "success":          True,
            "modification_id":  modification_id,
            "verdict":          cached["verdict"],
            "verdict_color":    _get_verdict_emoji(cached["verdict"]),
            "reasoning":        cached["reasoning"],
            "citations":        cached.get("citations", []),
            "source":           "cache",
            "corrected_name":   cached.get("corrected_name") or request.replacement_exercise,
            "cached_date":      cached.get("timestamp"),
            "can_proceed":      cached["verdict"] in ["green", "yellow"],
        }

    try:
        result = validator.validate_exercise_swap(
            original=request.original_exercise,
            replacement=request.replacement_exercise,
            reason=request.reason,
            goal=request.goal
        )

        if cache:
            cache.save_validation(
                request.original_exercise, request.replacement_exercise,
                request.reason, request.goal, result
            )

        db_save_cache(
            cache_key=m_cache_key,
            meta={
                "original":    request.original_exercise,
                "replacement": request.replacement_exercise,
                "reason":      request.reason,
                "goal":        request.goal,
            },
            validation_result=result
        )

        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "success":          True,
            "modification_id":  modification_id,
            "verdict":          result["verdict"],
            "verdict_color":    _get_verdict_emoji(result["verdict"]),
            "reasoning":        result["reasoning"],
            "citations":        result.get("citations", []),
            "source":           "perplexity_api",
            "corrected_name":   result.get("corrected_name") or request.replacement_exercise,
            "adjustments":      result.get("adjustments", {}),
            "can_proceed":      result["verdict"] in ["green", "yellow"],
            "warning":          "Proceed with caution - suboptimal substitution" if result["verdict"] == "yellow" else None,
        }

    except Exception as e:
        print("❌ VALIDATION CRASH:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}. See server logs for traceback."
        )


# ---------------------------------------------------------------------------
# POST /apply_modification
# ---------------------------------------------------------------------------
@app.post("/apply_modification")
async def apply_modification(
    request: ApplyModificationRequest,
    user_id: str = Depends(get_current_user)
):
    if modifier is None:
        raise HTTPException(status_code=503, detail="Workout modification temporarily unavailable.")

    if request.workout_id not in workout_sessions:
        raise HTTPException(status_code=404, detail=f"Workout '{request.workout_id}' not found")

    original_workout = workout_sessions[request.workout_id]

    if not _find_exercise_in_plan(original_workout, request.original_exercise):
        raise HTTPException(
            status_code=400,
            detail=f"Exercise '{request.original_exercise}' not found in any session of this workout."
        )

    if request.verdict.lower() not in ["green", "yellow"]:
        raise HTTPException(status_code=400, detail=f"Cannot apply '{request.verdict}' verdict")

    try:
        modified_workout = modifier.apply_modification(
            original_workout=original_workout,
            original_exercise=request.original_exercise,
            replacement_exercise=request.replacement_exercise,
            verdict=request.verdict,
            reasoning=request.reasoning,
            citations=request.citations,
            adjustments=request.adjustments
        )

        new_workout_id                   = modified_workout["workout_id"]
        workout_sessions[new_workout_id] = modified_workout

        save_workout(
            user_id=user_id,
            workout_id=new_workout_id,
            request_payload={"source": "modification", "parent_workout_id": request.workout_id},
            data=modified_workout,
        )

        return {
            "success":              True,
            "original_workout_id":  request.workout_id,
            "new_workout_id":       new_workout_id,
            "modified_workout":     modified_workout,
            "modification_summary": {
                "exercise_changed":    f"{request.original_exercise} → {request.replacement_exercise}",
                "verdict":             request.verdict,
                "total_modifications": len(modified_workout.get("modification_history", [])),
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modification failed: {str(e)}")


# ---------------------------------------------------------------------------
# POST /validate_swap
# ---------------------------------------------------------------------------
@app.post("/validate_swap")
async def validate_swap(request: ValidateSwapRequest):
    if not validator:
        raise HTTPException(
            status_code=503,
            detail="Validation system not configured. Set PERPLEXITY_API_KEY environment variable."
        )
    try:
        result = validator.validate_exercise_swap(
            original=request.original_exercise,
            replacement=request.replacement_exercise,
            reason=request.reason,
            goal=str(request.goal.value)
        )
        return {
            "verdict":       result["verdict"].upper(),
            "verdict_color": _get_verdict_emoji(result["verdict"]),
            "reasoning":     result["reasoning"],
            "citations":     result.get("citations", []),
            "can_proceed":   result["verdict"] in ["green", "yellow"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Swap validation error: {str(e)}")


# ---------------------------------------------------------------------------
# GET /test/{goal}  - no-auth smoke test, reflects real output shape
# ---------------------------------------------------------------------------
@app.get("/test/{goal}")
async def test_goal(
    goal: str,
    equipment: Optional[str] = "gym",
    experience: Optional[str] = "intermediate"
):
    try:
        weekly = generator.generate_weekly_plan(
            goal.lower(), equipment.lower(), experience.lower()
        )
        monday = weekly["weekly_plan"].get("monday", {})
        return {
            "goal":                  goal,
            "equipment":             equipment,
            "experience":            experience,
            "success":               True,
            "split_type":            weekly.get("split_type"),
            "training_days_per_week": weekly.get("training_days_per_week"),
            "total_duration_minutes": weekly.get("total_duration_minutes", 60),
            "prescription_source":   weekly.get("prescription_source", "N/A"),
            "evidence_level":        weekly.get("evidence_level"),
            "sample_session": {
                "day":          "monday",
                "session_name": monday.get("session_name"),
                "session_type": monday.get("session_type"),
                "exercises":    monday.get("exercises", []),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status":               "healthy",
        "timestamp":            datetime.now().isoformat(),
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals":      list(generator.prescriptions.keys()),
        "generator_ready":      True,
        "validation_ready":     validator is not None,
        "cache_ready":          cache is not None,
        "active_sessions":      len(workout_sessions),
    }

#minimal endpoint for cron-jobs
@app.get("/ping")
def ping():
    return {"status": "alive"}


# ---------------------------------------------------------------------------
# DELETE /clear_cache
# ---------------------------------------------------------------------------
@app.delete("/clear_cache")
def clear_cache():
    """Dev-only: Clear prescription validation cache."""
    try:
        from db import validation_cache_col
        if validation_cache_col is not None:
            validation_cache_col.delete_many({})
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /workouts
# ---------------------------------------------------------------------------
@app.get("/workouts")
async def list_workouts_handler(
    user_id: str = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List user's workout history, newest first."""
    return list_workouts(user_id, limit)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting FitApp Workout Generator API v2.0...")
    print("📖 Interactive docs: http://127.0.0.1:8000/docs")
    print(f"🔬 Validation system: {'✅ Ready' if validator else '⚠️  Not configured'}")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")

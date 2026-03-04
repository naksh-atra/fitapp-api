"""
FitApp Workout Generator API v1.0
Science-based workouts powered by YAML research prescriptions
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import uvicorn
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from enum import Enum
from auth import get_current_user, create_access_token

load_dotenv(
    dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env.local",
    override=True
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    ResearchValidator  = None
    ValidationCache    = None
    PrescriptionValidator = None

from repositories import save_workout, get_workout                        # NEW

app = FastAPI(
    title="🎯 FitApp Workout Generator API",
    description="Science-based workout generator with research-validated modifications\n\n4 goals: hypertrophy, strength, endurance, fatloss",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    prescription_validator = PrescriptionValidator()                      # CHANGED: no cache_path arg
    print("✓ Prescription validator initialized")
except Exception as e:
    print(f"⚠ Prescription validator failed: {e}")
    prescription_validator = None

validator = ResearchValidator() if ResearchValidator else None
cache     = ValidationCache()   if ValidationCache   else None

workout_sessions = {}


# --- Enums ---
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
    week:       Optional[int] = Field(default=1, ge=1, le=52)

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


@app.get("/")
async def root():
    return {
        "message": "🎯 FitApp Workout Generator API v1.0 - LIVE ✅",
        "status": "healthy",
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals": list(generator.prescriptions.keys()),
        "features": {
            "workout_generation":   "✅ Operational",
            "workout_modification": "✅ Ready" if modifier else "⚠️ Manual only",
            "modification_validation": "✅ Operational" if validator else "⚠️  Not configured",
            "research_citations":   "✅ Included"
        },
        "endpoints": {
            "generate_workout":      "POST /generate_workout",
            "validate_modification": "POST /validate_modification",
            "apply_modification":    "POST /apply_modification",
            "get_workout":           "GET /workouts/{workout_id}",        # NEW
            "test_goal":             "GET /test/{goal}",
            "docs":                  "/docs",
            "health":                "/health"
        },
        "example_flow": {
            "1_generate": "POST /generate_workout {\"goal\":\"hypertrophy\"}",
            "2_validate": "POST /validate_modification {\"workout_id\":\"...\", \"original_exercise\":\"Barbell Squat\", \"replacement_exercise\":\"Leg Press\", \"reason\":\"knee_pain\"}",
            "3_apply":    "POST /apply_modification {\"workout_id\":\"...\", \"modification_id\":\"...\"}"
        }
    }


@app.post("/generate_workout")
async def generate_workout(request: WorkoutRequest, user_id: str = Depends(get_current_user)):
    """Generate complete science-based workout from YAML prescriptions"""
    try:
        workout    = generator.generate_workout(
            goal=request.goal.lower(),
            equipment=request.equipment.lower(),
            experience=request.experience.lower(),
            week=request.week
        )

        workout_id = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workout["workout_id"] = workout_id

        if prescription_validator:
            validation_result = prescription_validator.validate_prescription(
                goal=request.goal,
                exercises=workout['exercises'],
                equipment=request.equipment,
                experience=request.experience
            )
            workout['research_validation'] = {
                "validated":        validation_result['validated'],
                "evidence_level":   validation_result['confidence'].upper(),
                "evidence_summary": validation_result['evidence_summary'],
                "citations":        validation_result['citations'],
                "validated_at":     validation_result['validated_at']
            }
            workout['evidence_level']        = validation_result['confidence'].upper()
            workout['citations']             = validation_result['citations']
            workout['prescription_source']   = f"Research-validated {request.goal} protocol (2023-2025)"
            workout['validation_source']     = validation_result.get('source', '')   # NEW: needed for cache test

        workout_sessions[workout_id] = workout

        # NEW: persist to MongoDB
        save_workout(
            user_id         = user_id,
            workout_id      = workout_id,
            request_payload = request.dict(),
            data            = workout,
        )

        return {
            "status":              "success",
            "message":             f"Research-validated {request.goal} workout generated",
            "workout_id":          workout_id,
            "data":                workout,
            "modification_enabled": modifier is not None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Goal '{request.goal}' not found. Available: {list(generator.prescriptions.keys())}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.post("/validate_modification")
async def validate_modification(request: ModificationRequest):
    if not validator:
        raise HTTPException(status_code=503, detail="Validation system not configured. Set PERPLEXITY_API_KEY environment variable.")

    if request.workout_id not in workout_sessions:
        raise HTTPException(status_code=404, detail=f"Workout ID '{request.workout_id}' not found. Generate a workout first.")

    cached = cache.get_cached_validation(
        request.original_exercise, request.replacement_exercise,
        request.reason, request.goal
    ) if cache else None

    if cached:
        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "success":       True,
            "modification_id": modification_id,
            "verdict":       cached['verdict'],
            "verdict_color": _get_verdict_emoji(cached['verdict']),
            "reasoning":     cached['reasoning'],
            "citations":     cached.get('citations', []),
            "source":        "cache",
            "cached_date":   cached.get('timestamp'),
            "can_proceed":   cached['verdict'] in ['green', 'yellow']
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

        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            "success":         True,
            "modification_id": modification_id,
            "verdict":         result['verdict'],
            "verdict_color":   _get_verdict_emoji(result['verdict']),
            "reasoning":       result['reasoning'],
            "citations":       result.get('citations', []),
            "source":          "perplexity_api",
            "adjustments":     result.get('adjustments', {}),
            "can_proceed":     result['verdict'] in ['green', 'yellow'],
            "warning":         "Proceed with caution - suboptimal substitution" if result['verdict'] == 'yellow' else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}. Unable to validate with research API.")


@app.post("/apply_modification")
async def apply_modification(request: ApplyModificationRequest, user_id: str = Depends(get_current_user)):
    if modifier is None:
        raise HTTPException(status_code=503, detail="Workout modification temporarily unavailable.")

    if request.workout_id not in workout_sessions:
        raise HTTPException(status_code=404, detail=f"Workout '{request.workout_id}' not found")

    original_workout = workout_sessions[request.workout_id]
    exercise_found   = any(
        ex['name'].lower() == request.original_exercise.lower()
        for ex in original_workout.get('exercises', [])
    )
    if not exercise_found:
        raise HTTPException(status_code=400, detail=f"Exercise '{request.original_exercise}' not in workout")

    if request.verdict.lower() not in ['green', 'yellow']:
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

        new_workout_id                    = modified_workout['workout_id']
        workout_sessions[new_workout_id]  = modified_workout

        # NEW: persist modified workout to MongoDB
        save_workout(
            user_id         = user_id,
            workout_id      = new_workout_id,
            request_payload = {"source": "modification", "parent_workout_id": request.workout_id},
            data            = modified_workout,
        )

        return {
            "success":              True,
            "original_workout_id":  request.workout_id,
            "new_workout_id":       new_workout_id,
            "modified_workout":     modified_workout,
            "modification_summary": {
                "exercise_changed":    f"{request.original_exercise} → {request.replacement_exercise}",
                "verdict":             request.verdict,
                "total_modifications": len(modified_workout.get('modification_history', []))
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modification failed: {str(e)}")


def _get_verdict_emoji(verdict: str) -> str:
    return {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(verdict.lower(), '⚪')


@app.post("/validate_swap")
async def validate_swap(request: ValidateSwapRequest):
    if not validator:
        raise HTTPException(status_code=503, detail="Validation system not configured. Set PERPLEXITY_API_KEY environment variable.")

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
            "can_proceed":   result["verdict"] in ["green", "yellow"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Swap validation error: {str(e)}")


@app.get("/test/{goal}")
async def test_goal(goal: str, equipment: Optional[str] = "gym", experience: Optional[str] = "intermediate"):
    try:
        workout = generator.generate_workout(goal.lower(), equipment.lower(), experience.lower())
        return {
            "goal":               goal,
            "equipment":          equipment,
            "experience":         experience,
            "success":            True,
            "exercise_count":     len(workout["exercises"]),
            "duration_minutes":   workout.get("total_duration_minutes", 60),
            "sample_exercise":    workout["exercises"][0] if workout["exercises"] else None,
            "prescription_source": workout.get("prescription_source", "N/A")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        "active_sessions":      len(workout_sessions)
    }


@app.delete("/clear_cache")
def clear_cache():
    """Dev-only: Clear prescription cache"""
    try:
        from db import validation_cache_col                               # NEW
        validation_cache_col.delete_many({})                             # NEW
        if prescription_validator:
            pass  # no in-memory cache to clear anymore                  # CHANGED
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NEW: Retrieve persisted workout by ID
@app.get("/workouts/{workout_id}")
def fetch_workout(workout_id: str, user_id: str = Depends(get_current_user)):
    """Retrieve a previously generated workout from MongoDB"""
    data = get_workout("anonymous", workout_id)
    if not data:
        raise HTTPException(status_code=404, detail="Workout not found")
    return {"workout_id": workout_id, "data": data}


if __name__ == "__main__":
    print("🚀 Starting FitApp Workout Generator API...")
    print("📖 Interactive docs: http://127.0.0.1:8000/docs")
    print(f"🔬 Validation system: {'✅ Ready' if validator else '⚠️  Not configured'}")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")

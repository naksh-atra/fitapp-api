"""
FitApp Workout Generator API v1.0
Science-based workouts powered by YAML research prescriptions
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import uvicorn
import sys
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.local")

# Add parent directory to path for generator import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from generator.workout_engine import WorkoutGenerator
    print("✓ WorkoutGenerator imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: python src/generator/workout_engine.py first to test")

# NEW: Import validation components
try:
    from validation.research_validator import ResearchValidator
    from validation.validation_cache import ValidationCache
    print("✓ Validation system imported successfully")
except ImportError as e:
    print(f"⚠️  Validation system not yet implemented: {e}")
    ResearchValidator = None
    ValidationCache = None

app = FastAPI(
    title="🎯 FitApp Workout Generator API",
    description="Science-based workout generator with research-validated modifications\n\n4 goals: hypertrophy, strength, endurance, fatloss",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize generator
generator = WorkoutGenerator()

# NEW: Initialize validation system (if available)
validator = ResearchValidator() if ResearchValidator else None
cache = ValidationCache() if ValidationCache else None

# NEW: In-memory session storage (replace with Redis/DB for production)
workout_sessions = {}


class WorkoutRequest(BaseModel):
    goal: str  # Required: hypertrophy, strength, endurance, fatloss
    equipment: Optional[str] = "gym"  # gym, home
    experience: Optional[str] = "intermediate"  # beginner, intermediate, advanced
    week: Optional[int] = 1


# NEW: Validation request models
class ModificationRequest(BaseModel):
    workout_id: str  # From original generation
    original_exercise: str
    replacement_exercise: str
    reason: str  # e.g., "knee_pain", "no_equipment", "preference"
    goal: Optional[str] = "hypertrophy"


class ApplyModificationRequest(BaseModel):
    workout_id: str
    modification_id: str  # From validation response
    accept: bool = True  # Whether to proceed with modification


@app.get("/")
async def root():
    """API root endpoint - shows available goals and usage"""
    return {
        "message": "🎯 FitApp Workout Generator API v1.0 - LIVE ✅",
        "status": "healthy",
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals": list(generator.prescriptions.keys()),
        "features": {
            "workout_generation": "✅ Operational",
            "modification_validation": "✅ Operational" if validator else "⚠️  Not configured",
            "research_citations": "✅ Included"
        },
        "endpoints": {
            "generate_workout": "POST /generate_workout",
            "validate_modification": "POST /validate_modification",  # NEW
            "apply_modification": "POST /apply_modification",  # NEW
            "test_goal": "GET /test/{goal}",
            "docs": "/docs",
            "health": "/health"
        },
        "example_flow": {
            "1_generate": "POST /generate_workout {\"goal\":\"hypertrophy\"}",
            "2_validate": "POST /validate_modification {\"workout_id\":\"...\", \"original_exercise\":\"Barbell Squat\", \"replacement_exercise\":\"Leg Press\", \"reason\":\"knee_pain\"}",
            "3_apply": "POST /apply_modification {\"workout_id\":\"...\", \"modification_id\":\"...\"}"
        }
    }


@app.post("/generate_workout")
async def generate_workout(request: WorkoutRequest):
    """Generate complete science-based workout from YAML prescriptions"""
    try:
        workout = generator.generate_workout(
            goal=request.goal.lower(),
            equipment=request.equipment.lower(),
            experience=request.experience.lower(),
            week=request.week
        )
        
        # NEW: Generate workout ID and store in session
        workout_id = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workout["workout_id"] = workout_id
        workout_sessions[workout_id] = workout
        
        return {
            "success": True,
            "workout_id": workout_id,  # NEW: Return for modification tracking
            "data": workout,
            "prescription_evidence": workout.get("evidence_level", "High"),
            "source_file": workout.get("prescription_source", "N/A"),
            "exercise_count": len(workout["exercises"]),
            "total_duration_minutes": workout["total_duration_minutes"],
            "modification_enabled": validator is not None  # NEW: Tell frontend if modifications work
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Goal '{request.goal}' not found. Available: {list(generator.prescriptions.keys())}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


# NEW: Validation endpoint
@app.post("/validate_modification")
async def validate_modification(request: ModificationRequest):
    """
    Validate user's proposed exercise substitution using Perplexity API.
    Returns green/yellow/red verdict with research citations.
    """
    if not validator:
        raise HTTPException(
            status_code=503, 
            detail="Validation system not configured. Set PERPLEXITY_API_KEY environment variable."
        )
    
    # Check if workout exists
    if request.workout_id not in workout_sessions:
        raise HTTPException(status_code=404, detail=f"Workout ID '{request.workout_id}' not found. Generate a workout first.")
    
    # Check cache first
    cached = cache.get_cached_validation(
        request.original_exercise,
        request.replacement_exercise,
        request.reason,
        request.goal
    ) if cache else None
    
    if cached:
        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "success": True,
            "modification_id": modification_id,
            "verdict": cached['verdict'],
            "verdict_color": _get_verdict_emoji(cached['verdict']),
            "reasoning": cached['reasoning'],
            "citations": cached.get('citations', []),
            "source": "cache",
            "cached_date": cached.get('timestamp'),
            "can_proceed": cached['verdict'] in ['green', 'yellow']
        }
    
    # Call Perplexity API for new validation
    try:
        result = validator.validate_exercise_swap(
            original=request.original_exercise,
            replacement=request.replacement_exercise,
            reason=request.reason,
            goal=request.goal
        )
        
        # Cache the result
        if cache:
            cache.save_validation(
                request.original_exercise,
                request.replacement_exercise,
                request.reason,
                request.goal,
                result
            )
        
        modification_id = f"mod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "success": True,
            "modification_id": modification_id,
            "verdict": result['verdict'],
            "verdict_color": _get_verdict_emoji(result['verdict']),
            "reasoning": result['reasoning'],
            "citations": result.get('citations', []),
            "source": "perplexity_api",
            "adjustments": result.get('adjustments', {}),
            "can_proceed": result['verdict'] in ['green', 'yellow'],
            "warning": "Proceed with caution - suboptimal substitution" if result['verdict'] == 'yellow' else None
        }
        
    except Exception as e:
        # Fallback: return cautious yellow verdict if API fails
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}. Unable to validate with research API."
        )


# NEW: Apply modification endpoint
@app.post("/apply_modification")
async def apply_modification(request: ApplyModificationRequest):
    """
    Apply validated modification to workout.
    Only works if validation returned green or yellow and user accepts.
    """
    if request.workout_id not in workout_sessions:
        raise HTTPException(status_code=404, detail=f"Workout ID '{request.workout_id}' not found")
    
    if not request.accept:
        return {
            "success": False,
            "message": "Modification cancelled by user",
            "workout": workout_sessions[request.workout_id]
        }
    
    # TODO: Implement workout modification logic
    # For now, return placeholder
    return {
        "success": True,
        "message": "⚠️  Modification application not yet implemented. Next sprint.",
        "workout_id": request.workout_id,
        "modification_id": request.modification_id,
        "status": "pending_implementation"
    }


# NEW: Helper function
def _get_verdict_emoji(verdict: str) -> str:
    """Return color emoji for verdict"""
    return {
        'green': '🟢',
        'yellow': '🟡',
        'red': '🔴'
    }.get(verdict.lower(), '⚪')


@app.get("/test/{goal}")
async def test_goal(goal: str, equipment: Optional[str] = "gym", experience: Optional[str] = "intermediate"):
    """Quick test endpoint - returns workout summary"""
    try:
        workout = generator.generate_workout(goal.lower(), equipment.lower(), experience.lower())
        return {
            "goal": goal,
            "equipment": equipment,
            "experience": experience,
            "success": True,
            "exercise_count": len(workout["exercises"]),
            "duration_minutes": workout.get("total_duration_minutes", 60),
            "sample_exercise": workout["exercises"][0] if workout["exercises"] else None,
            "prescription_source": workout.get("prescription_source", "N/A")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check for deployment monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals": list(generator.prescriptions.keys()),
        "generator_ready": True,
        "validation_ready": validator is not None,
        "cache_ready": cache is not None,
        "active_sessions": len(workout_sessions)
    }


if __name__ == "__main__":
    print("🚀 Starting FitApp Workout Generator API...")
    print("📖 Interactive docs: http://127.0.0.1:8000/docs")
    print(f"🔬 Validation system: {'✅ Ready' if validator else '⚠️  Not configured'}")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

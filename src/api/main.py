"""
FitApp Workout Generator API v1.0
Science-based workouts powered by YAML research prescriptions
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
import os
from pathlib import Path

# Add parent directory to path for generator import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from generator.workout_engine import WorkoutGenerator
    print("✓ WorkoutGenerator imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: python src/generator/workout_engine.py first to test")

app = FastAPI(
    title="🎯 FitApp Workout Generator API",
    description="Science-based workout generator using research-derived YAML prescriptions\n\n4 goals: hypertrophy, strength, endurance, fatloss",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize generator
generator = WorkoutGenerator()

class WorkoutRequest(BaseModel):
    goal: str  # Required: hypertrophy, strength, endurance, fatloss
    equipment: Optional[str] = "gym"  # gym, home
    experience: Optional[str] = "intermediate"  # beginner, intermediate, advanced
    week: Optional[int] = 1

@app.get("/")
async def root():
    """API root endpoint - shows available goals and usage"""
    return {
        "message": "🎯 FitApp Workout Generator API v1.0 - LIVE ✅",
        "status": "healthy",
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals": list(generator.prescriptions.keys()),
        "endpoints": {
            "generate_workout": "POST /generate_workout",
            "test_goal": "GET /test/{goal}",
            "docs": "/docs",
            "health": "/health"
        },
        "example": "curl -X POST /generate_workout -d '{\"goal\":\"hypertrophy\"}'"
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
        return {
            "success": True,
            "data": workout,
            "prescription_evidence": workout.get("evidence_level", "High"),
            "source_file": workout.get("prescription_source", "N/A"),
            "exercise_count": len(workout["exercises"]),
            "total_duration_minutes": workout["total_duration_minutes"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Goal '{request.goal}' not found. Available: {list(generator.prescriptions.keys())}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

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
        "timestamp": "2025-12-20",
        "prescriptions_loaded": len(generator.prescriptions),
        "available_goals": list(generator.prescriptions.keys()),
        "generator_ready": True
    }

if __name__ == "__main__":
    print("🚀 Starting FitApp Workout Generator API...")
    print("📖 Interactive docs: http://127.0.0.1:8000/docs")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

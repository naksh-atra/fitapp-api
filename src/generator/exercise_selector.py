"""
Exercise selector: filters exercise database by goal, equipment, difficulty
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class ExerciseSelector:
    def __init__(self, db_path: str = "data/exercises/exercise_database.json"):
        self.db_path = Path(db_path)
        self.exercises = self._load_exercises()
    
    def _load_exercises(self) -> List[Dict]:
        """Load exercise database from JSON"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Exercise database not found: {self.db_path}")
        
        with open(self.db_path, 'r') as f:
            data = json.load(f)
        
        return data.get('exercises', [])
    
    def get_exercises(
        self,
        goal: str,
        category: Optional[str] = None,
        equipment: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Filter exercises by criteria and return top N
        """
        filtered = self.exercises
        
        # Filter by goal
        filtered = [ex for ex in filtered if goal.lower() in [g.lower() for g in ex.get('goals', [])]]
        
        # Filter by category
        if category:
            filtered = [ex for ex in filtered if ex.get('category', '').lower() == category.lower()]
        
        # Filter by equipment
        if equipment:
            equipment_lower = [eq.lower() for eq in equipment]
            filtered = [
                ex for ex in filtered 
                if all(req.lower() in equipment_lower for req in ex.get('equipment', []))
            ]
        
        # Filter by difficulty
        if difficulty:
            filtered = [ex for ex in filtered if ex.get('difficulty', '').lower() == difficulty.lower()]
        
        # Sort by rating (high to low)
        filtered = sorted(filtered, key=lambda x: x.get('rating', 0), reverse=True)
        
        return filtered[:limit]

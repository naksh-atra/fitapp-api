"""
Workout Generator Engine
Loads YAML prescriptions and generates science-based workouts
"""

import yaml
import random
from typing import Dict, List, Any
from pathlib import Path

from .exercise_selector import ExerciseSelector


class WorkoutGenerator:
    def __init__(self, config_dir: str = "config/prescriptions"):
        self.config_dir = Path(config_dir)
        self.prescriptions = self._load_all_prescriptions()
    
    def _load_all_prescriptions(self) -> Dict[str, Dict]:
        """Load all 4 goal prescriptions"""
        goals = ['hypertrophy', 'strength', 'endurance', 'fatloss']
        prescriptions = {}
        
        for goal in goals:
            yaml_path = self.config_dir / f"{goal}.yaml"
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    prescriptions[goal] = yaml.safe_load(f)
                print(f"✓ Loaded {goal} prescription")
            else:
                print(f"⚠️ Missing {goal}.yaml")
        
        return prescriptions
    
    def generate_workout(self, goal: str, equipment: str = "gym", experience: str = "intermediate", week: int = 1) -> Dict:
        """Generate complete workout for specified goal"""
        if goal not in self.prescriptions:
            raise ValueError(f"Goal '{goal}' not found. Available: {list(self.prescriptions.keys())}")
        
        prescription = self.prescriptions[goal]
        workout = self._build_workout_structure(goal, equipment, experience, week)
        
        # Add exercises based on goal-specific logic
        if goal == "hypertrophy":
            workout['exercises'] = self._generate_hypertrophy_workout(prescription, equipment, experience)
        elif goal == "strength":
            workout['exercises'] = self._generate_strength_workout(prescription, equipment, experience)
        elif goal == "endurance":
            workout['exercises'] = self._generate_endurance_workout(prescription, equipment)
        elif goal == "fatloss":
            workout['exercises'] = self._generate_fatloss_workout(prescription, equipment)
        
        # Add prescription metadata
        workout['prescription_source'] = prescription['metadata']['source_file']
        workout['evidence_level'] = prescription['metadata']['evidence_level']
        
        return workout
    
    def _build_workout_structure(self, goal: str, equipment: str, experience: str, week: int) -> Dict:
        """Build base workout structure"""
        return {
            'goal': goal,
            'equipment': equipment,
            'experience': experience,
            'week': week,
            'session_type': 'main',
            'total_duration_minutes': 60,
            'exercises': [],
            'notes': f"Week {week} progression from {self.prescriptions[goal]['metadata']['source_file']}"
        }
    
    def _generate_hypertrophy_workout(self, prescription: Dict, equipment: str, experience: str) -> List[Dict]:
        """Generate hypertrophy-specific workout"""
        compound_params = prescription['hypertrophy']['compound_lifts']['parameters']
        isolation_params = prescription['hypertrophy']['isolation_lifts']['parameters']
        
        exercises = []
        
        # Compound lifts (upper + lower)
        compound_exercises = self._get_exercises_by_equipment('compound', equipment)
        for i, exercise in enumerate(compound_exercises[:3]):  # 3 compound lifts
            exercises.append({
                'name': exercise,
                'type': 'compound',
                'sets': self._parse_range(compound_params['sets']),
                'reps': self._parse_range(compound_params['reps']),
                'tempo': compound_params['tempo'],
                'rest_seconds': self._parse_range(compound_params['rest_seconds']),
                'rpe': compound_params['intensity_rpe']
            })
        
        # Isolation accessories
        isolation_exercises = self._get_exercises_by_equipment('isolation', equipment)
        for i, exercise in enumerate(isolation_exercises[:3]):  # 3 isolation
            exercises.append({
                'name': exercise,
                'type': 'isolation',
                'sets': self._parse_range(isolation_params['sets']),
                'reps': self._parse_range(isolation_params['reps']),
                'tempo': isolation_params['tempo'],
                'rest_seconds': self._parse_range(isolation_params['rest_seconds']),
                'rpe': isolation_params['intensity_rpe']
            })
        
        return exercises
    
    def _generate_strength_workout(self, prescription: Dict, equipment: str, experience: str) -> List[Dict]:
        """Generate strength-specific workout"""
        main_params = prescription['strength']['main_lifts']['parameters']
        
        # Main competition lifts
        main_lifts = ['Back Squat', 'Bench Press', 'Deadlift', 'Overhead Press']
        exercises = []
        
        for lift in main_lifts[:3]:  # 3 main lifts per session
            exercises.append({
                'name': lift,
                'type': 'main_competition',
                'sets': self._parse_range(main_params['sets']),
                'reps': self._parse_range(main_params['reps_max_strength']),
                'percent_1rm': main_params['weight_1rm_percent_1_3_reps'],
                'rpe': main_params['intensity_rpe'],
                'rest_seconds': self._parse_range(main_params['rest_seconds'])
            })
        
        return exercises
    
    def _generate_endurance_workout(self, prescription: Dict, equipment: str) -> List[Dict]:
        """Generate endurance-specific workout"""
        zone2_params = prescription['endurance']['zone_2_aerobic_base']['parameters']
        
        return [{
            'name': f"{equipment.capitalize()} - Zone 2 Aerobic Base",
            'type': 'cardio_continuous',
            'duration_minutes': self._parse_range(zone2_params['duration_minutes']),
            'intensity': f"{zone2_params['intensity_hrmax_percent']} HRmax",
            'cadence': zone2_params['cadence_pace'],
            'frequency': zone2_params['frequency']
        }]
    
    def _generate_fatloss_workout(self, prescription: Dict, equipment: str) -> List[Dict]:
        """Generate fat loss-specific workout"""
        hiit_params = prescription['fatloss']['hiit_circuits']['parameters']
        
        return [{
            'name': f"HIIT Circuit ({equipment})",
            'type': 'hiit_circuit',
            'work_interval_seconds': self._parse_range(hiit_params['work_interval_seconds']),
            'rest_interval_seconds': self._parse_range(hiit_params['rest_interval_seconds']),
            'rounds': self._parse_range(hiit_params['rounds']),
            'rpe': hiit_params['intensity_rpe'],
            'exercises_per_round': hiit_params['exercises_per_round']
        }]
    
    def _get_exercises_by_equipment(self, exercise_type: str, equipment: str) -> List[str]:
        """Get exercise list by type and equipment (placeholder - expand later)"""
        exercise_db = {
            'gym': {
                'compound': ['Barbell Bench Press', 'Back Squat', 'Deadlift', 'Pull Up', 'Overhead Press'],
                'isolation': ['Bicep Curl', 'Tricep Extension', 'Lateral Raise', 'Leg Extension']
            },
            'home': {
                'compound': ['Push Up', 'Air Squat', 'Inverted Row', 'Pike Push Up'],
                'isolation': ['Bodyweight Curl', 'Tricep Dips', 'Side Plank']
            }
        }
        return exercise_db.get(equipment, exercise_db['gym']).get(exercise_type, [])
    
    def _parse_range(self, range_str: str) -> List[int]:
        """Parse ANY range format → [low, high]
        Handles: '3-5', '1-3 reps', '30-90 minutes', '85-95%', etc."""
        
        # Clean up all common suffixes/prefixes
        range_str = range_str.replace('%', '').replace('1RM', '').replace('HRmax', '')
        range_str = range_str.replace(' per ', '').replace(' per exercise', '').replace(' per set', '')
        range_str = range_str.replace(' reps', '').replace(' minutes', '').replace(' seconds', '').strip()
        
        if '-' in range_str:
            parts = range_str.split('-')
            low_str = parts[0].strip()
            high_str = parts[1].strip()
            
            # Extract numbers only
            import re
            low = int(re.search(r'\d+', low_str).group())
            high = int(re.search(r'\d+', high_str).group())
            return [low, high]
        else:
            # Single number
            import re
            num = int(re.search(r'\d+', range_str).group())
            return [num, num]



# Test function
if __name__ == "__main__":
    generator = WorkoutGenerator()
    
    # Test hypertrophy workout
    hyp_workout = generator.generate_workout("hypertrophy", "gym", "intermediate", week=1)
    print("=== HYPERTROPHY WORKOUT ===")
    print(f"Goal: {hyp_workout['goal']}")
    print(f"Exercises: {len(hyp_workout['exercises'])}")
    print(f"Source: {hyp_workout['prescription_source']}")
    
    # Test strength workout
    strength_workout = generator.generate_workout("strength", "gym", "intermediate", week=1)
    print("\n=== STRENGTH WORKOUT ===")
    print(f"Goal: {strength_workout['goal']}")
    print(f"Exercises: {len(strength_workout['exercises'])}")
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
        """Generate strength-specific workout (>=4 exercises)"""
        main_params = prescription['strength']['main_lifts']['parameters']
        accessory_params = prescription['strength']['accessory_lifts']['parameters']

        # Main competition lifts (gym) or alternatives (home)
        if equipment == 'home':
            main_lifts = ['Goblet Squat', 'Pike Push Up', 'Romanian Deadlift (Dumbbell)', 'Dumbbell Press']
        else:
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

        # 1 accessory / weak-point lift
        accessory = 'Paused Squat' if equipment == 'gym' else 'Bulgarian Split Squat'
        exercises.append({
            'name': accessory,
            'type': 'accessory',
            'sets': self._parse_range(accessory_params['sets']),
            'reps': [6, 10],  # Accessory rep range for strength (6-10)
            'rpe': accessory_params['intensity_rpe'],
            'rest_seconds': self._parse_range(accessory_params['rest_seconds'])
        })

        return exercises
    
    def _generate_endurance_workout(self, prescription: Dict, equipment: str) -> List[Dict]:
        """Generate endurance-specific workout with >=4 exercises"""
        zone2_params  = prescription['endurance']['zone_2_aerobic_base']['parameters']
        thresh_params = prescription['endurance']['lactate_threshold_tempo']['parameters']

        endurance_exercises_db = {
            'gym': [
                'Treadmill Zone-2 Run',
                'Rowing Machine Intervals',
                'Stationary Bike Tempo',
                'Elliptical Steady-State',
                'Stair Climber Intervals',
            ],
            'home': [
                'Outdoor Zone-2 Run',
                'Jump Rope Intervals',
                'Bodyweight Squat Circuits',
                'Step-Up Aerobic Intervals',
                'High Knees Circuit',
            ]
        }

        exercises_list = endurance_exercises_db.get(equipment, endurance_exercises_db['gym'])

        exercises = []
        # 3 Zone-2 / aerobic base entries
        for name in exercises_list[:3]:
            exercises.append({
                'name': name,
                'type': 'cardio_aerobic',
                'duration_minutes': self._parse_range(zone2_params['duration_minutes']),
                'intensity': f"{zone2_params['intensity_hrmax_percent']} HRmax",
                'sets': [1, 1],
                'reps': [1, 1],
                'rpe': '6-7',
                'rest_seconds': [60, 120],
            })
        # 1 threshold interval entry
        exercises.append({
            'name': f'Lactate Threshold Intervals ({equipment.capitalize()})',
            'type': 'cardio_threshold',
            'duration_intervals': thresh_params['duration_intervals'],
            'intensity': f"{thresh_params['intensity_hrmax_percent']} HRmax",
            'sets': [1, 1],
            'reps': [1, 1],
            'rpe': '7-8',
            'rest_seconds': [120, 240],  # 2-4 minutes recovery between intervals
        })


        return exercises
    def _generate_fatloss_workout(self, prescription: Dict, equipment: str) -> List[Dict]:
        """Generate fat loss-specific workout with >=4 exercises"""
        hiit_params  = prescription['fatloss']['hiit_circuits']['parameters']
        metcon_params = prescription['fatloss']['metcon']['parameters']

        fatloss_exercises_db = {
            'gym': [
                'Kettlebell Swing',
                'Battle Ropes Sprint',
                'Barbell Thruster',
                'Box Jump',
                'Rowing Machine Sprint',
            ],
            'home': [
                'Burpees',
                'Jump Squat',
                'Push Up to Mountain Climber',
                'High Knees Sprint',
                'Bodyweight Lunge Jump',
            ]
        }

        exercises_list = fatloss_exercises_db.get(equipment, fatloss_exercises_db['gym'])

        exercises = []
        for name in exercises_list[:4]:
            exercises.append({
                'name': name,
                'type': 'hiit_compound',
                'work_interval_seconds': self._parse_range(hiit_params['work_interval_seconds']),
                'rest_interval_seconds': self._parse_range(hiit_params['rest_interval_seconds']),
                'rounds': self._parse_range(hiit_params['rounds']),
                'sets': self._parse_range(hiit_params['rounds']),
                'reps': [10, 15],
                'rpe': hiit_params['intensity_rpe'],
                'rest_seconds': self._parse_range(hiit_params['rest_interval_seconds']),
            })

        # Add one MetCon finisher
        exercises.append({
            'name': f'MetCon AMRAP Finisher ({equipment.capitalize()})',
            'type': 'metcon_amrap',
            'duration_minutes': 15,
            'sets': [1, 1],
            'reps': [1, 1],
            'rpe': metcon_params['intensity_rpe'],
            'rest_seconds': [120, 180],  # 2-3 minutes between rounds
        })

        return exercises
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
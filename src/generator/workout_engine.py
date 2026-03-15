"""
Workout Generator Engine
Loads YAML prescriptions and generates science-based workouts
"""

import yaml
import random
import re
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
    
    def generate_workout(self, goal: str, equipment: str = "gym", experience: str = "intermediate") -> Dict:
        """Generate complete workout for specified goal"""
        if goal not in self.prescriptions:
            raise ValueError(f"Goal '{goal}' not found. Available: {list(self.prescriptions.keys())}")
        
        prescription = self.prescriptions[goal]
        workout = self._build_workout_structure(goal, equipment, experience)
        
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
    
    def _build_workout_structure(self, goal: str, equipment: str, experience: str) -> Dict:
        """Build base workout structure"""
        return {
            'goal': goal,
            'equipment': equipment,
            'experience': experience,
            'session_type': 'main',
            'total_duration_minutes': 60,
            'exercises': [],
            'notes': f"Evidence-based prescription from {self.prescriptions[goal]['metadata']['source_file']}"
        }
    
    def _generate_hypertrophy_workout(self, prescription: Dict, equipment: str, experience: str) -> List[Dict]:
        """Generate hypertrophy-specific workout with randomized cues"""
        compound_params = prescription['hypertrophy']['compound_lifts']['parameters']
        isolation_params = prescription['hypertrophy']['isolation_lifts']['parameters']
        
        exercises = []
        
        # 1. Compound lifts (upper + lower)
        compound_names = self._get_exercises_by_equipment('compound', equipment)
        for i, name in enumerate(compound_names[:3]):
            reps_base = [6, 8] if i == 0 else [8, 10]
            exercises.append({
                'name': name,
                'type': 'compound',
                'sets': self._parse_range(compound_params['sets']),
                'reps': reps_base,
                'tempo': compound_params['tempo'],
                'rest_seconds': self._parse_range(compound_params['rest_seconds']),
                'rpe': compound_params['intensity_rpe'],
                'pro_notes': random.choice([
                    "Maintain spinal neutrality and brace core throughout.",
                    "Controlled eccentric phase (3s) to enhance mechanical tension.",
                    "Explosive concentric phase without losing form.",
                    "Full range of motion - reach deep lengthening phase."
                ])
            })
        
        # 2. Isolation accessories
        isolation_names = self._get_exercises_by_equipment('isolation', equipment)
        for i, name in enumerate(isolation_names[:3]):
            reps_base = [10, 12] if i < 2 else [12, 15]
            exercises.append({
                'name': name,
                'type': 'isolation',
                'sets': self._parse_range(isolation_params['sets']),
                'reps': reps_base,
                'tempo': isolation_params['tempo'],
                'rest_seconds': self._parse_range(isolation_params['rest_seconds']),
                'rpe': isolation_params['intensity_rpe'],
                'pro_notes': random.choice([
                    "Focus on maximum peak contraction and mind-muscle connection.",
                    "Internal cue: 'Squeeze the muscle' at the top of the rep.",
                    "Controlled tempo with 1s hold at the peak.",
                    "Ensure full range of motion in the lengthened position."
                ])
            })
        
        return exercises
    
    def _generate_strength_workout(self, prescription: Dict, equipment: str, experience: str) -> List[Dict]:
        """Generate strength-specific workout with randomized cues"""
        main_params = prescription['strength']['main_lifts']['parameters']
        accessory_params = prescription['strength']['accessory_lifts']['parameters']

        if equipment == 'home':
            main_lifts = ['Goblet Squat', 'Pike Push Up', 'Romanian Deadlift (Dumbbell)', 'Dumbbell Press']
        else:
            main_lifts = ['Back Squat', 'Bench Press', 'Deadlift', 'Overhead Press']

        exercises = []

        # Main lifts
        for i, lift in enumerate(main_lifts[:3]):
            # Heavier focus for the first lift
            reps = [1, 3] if i == 0 else [3, 5]
            exercises.append({
                'name': lift,
                'type': 'main_competition',
                'sets': self._parse_range(main_params['sets']),
                'reps': reps,
                'percent_1rm': main_params['weight_1rm_percent_1_3_reps'],
                'rpe': main_params['intensity_rpe'],
                'rest_seconds': [180, 300], # Longer rest for strength
                'pro_notes': random.choice([
                    "Maximum intent on the concentric phase.",
                    "Brace hard and squeeze the bar to maximize neural drive.",
                    "Focus on technical proficiency over absolute load.",
                    "Maintain total body tension throughout the lift."
                ])
            })

        # 1 accessory
        accessory = 'Paused Squat' if equipment == 'gym' else 'Bulgarian Split Squat'
        exercises.append({
            'name': accessory,
            'type': 'accessory',
            'sets': self._parse_range(accessory_params['sets']),
            'reps': [6, 10],
            'rpe': accessory_params['intensity_rpe'],
            'rest_seconds': self._parse_range(accessory_params['rest_seconds']),
            'pro_notes': "Focus on identifying and strengthening the technical weak point."
        })

        return exercises
    
    def _generate_endurance_workout(self, prescription: Dict, equipment: str) -> List[Dict]:
        """Generate endurance-specific workout"""
        zone2_params  = prescription['endurance']['zone_2_aerobic_base']['parameters']
        thresh_params = prescription['endurance']['lactate_threshold_tempo']['parameters']

        endurance_exercises_db = {
            'gym': ['Treadmill Run', 'Rowing Machine', 'Stationary Bike', 'Elliptical', 'Stair Climber'],
            'home': ['Outdoor Run', 'Jump Rope', 'Bodyweight Squats', 'Step-Ups', 'High Knees']
        }

        exercises_list = endurance_exercises_db.get(equipment, endurance_exercises_db['gym'])
        exercises = []

        for name in exercises_list[:3]:
            exercises.append({
                'name': f"{name} (Zone 2)",
                'type': 'cardio_aerobic',
                'duration_minutes': self._parse_range(zone2_params['duration_minutes']),
                'intensity': f"{zone2_params['intensity_hrmax_percent']} HRmax",
                'sets': [1, 1],
                'reps': [1, 1],
                'rpe': '6-7',
                'rest_seconds': [0, 0],
                'pro_notes': "Maintain a 'conversational' pace. Stay below lactate threshold."
            })
        
        exercises.append({
            'name': 'Threshold Intervals',
            'type': 'cardio_threshold',
            'duration_intervals': thresh_params['duration_intervals'],
            'intensity': f"{thresh_params['intensity_hrmax_percent']} HRmax",
            'sets': [1, 1],
            'reps': [1, 1],
            'rpe': '8-9',
            'rest_seconds': [120, 180],
            'pro_notes': "Pace should be 'comfortably hard'. Focus on consistent power output."
        })

        return exercises

    def _generate_fatloss_workout(self, prescription: Dict, equipment: str) -> List[Dict]:
        """Generate fat loss-specific workout"""
        hiit_params  = prescription['fatloss']['hiit_circuits']['parameters']
        
        fatloss_exercises_db = {
            'gym': ['Kettlebell Swing', 'Battle Ropes', 'Thrusters', 'Box Jumps'],
            'home': ['Burpees', 'Jump Squat', 'Mountain Climbers', 'Lunge Jumps']
        }

        exercises_list = fatloss_exercises_db.get(equipment, fatloss_exercises_db['gym'])
        exercises = []

        for name in exercises_list[:4]:
            exercises.append({
                'name': name,
                'type': 'hiit_compound',
                'work_interval_seconds': self._parse_range(hiit_params['work_interval_seconds']),
                'rest_interval_seconds': self._parse_range(hiit_params['rest_interval_seconds']),
                'rounds': [3, 5],
                'sets': [1, 1],
                'reps': [12, 15],
                'rpe': '9-10',
                'rest_seconds': self._parse_range(hiit_params['rest_interval_seconds']),
                'pro_notes': random.choice([
                    "Maintain maximum horizontal power and intensity.",
                    "Short rest to enhance EPOC (Afterburn effect).",
                    "Prioritize movement quality even under high fatigue.",
                    "Full effort on the work interval."
                ])
            })

        return exercises

    def _get_exercises_by_equipment(self, exercise_type: str, equipment: str) -> List[str]:
        """Get exercise list by type and equipment"""
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
        """Parse ANY range format → [low, high]"""
        if not isinstance(range_str, str): return [int(range_str), int(range_str)]
        
        range_str = range_str.replace('%', '').replace('1RM', '').replace('HRmax', '')
        range_str = range_str.split(' per ')[0].replace(' reps', '').replace(' minutes', '').strip()
        
        if '-' in range_str:
            parts = range_str.split('-')
            low = int(re.search(r'\d+', parts[0]).group())
            high = int(re.search(r'\d+', parts[1]).group())
            return [low, high]
        else:
            num = int(re.search(r'\d+', range_str).group())
            return [num, num]
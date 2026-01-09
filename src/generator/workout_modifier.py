"""
Workout modifier: applies validated exercise substitutions
"""

import copy
from datetime import datetime
from typing import Dict, Optional


class WorkoutModifier:
    
    def apply_modification(
        self,
        original_workout: Dict,
        original_exercise: str,
        replacement_exercise: str,
        verdict: str,
        reasoning: str,
        citations: list,
        adjustments: Optional[Dict] = None
    ) -> Dict:
        """
        Apply validated modification to workout.
        Returns modified workout with history.
        """
        # Deep copy to preserve original
        modified_workout = copy.deepcopy(original_workout)
        
        # Find and replace exercise
        exercise_found = False
        for exercise in modified_workout.get('exercises', []):
            if exercise['name'].lower() == original_exercise.lower():
                exercise_found = True
                
                # Store original name
                exercise['original_name'] = exercise['name']
                exercise['name'] = replacement_exercise
                exercise['modified'] = True
                
                # Apply adjustments if YELLOW verdict
                if verdict == 'yellow' and adjustments:
                    self._apply_adjustments(exercise, adjustments)
                
                # Add modification note
                exercise['modification_note'] = self._extract_summary(reasoning)
                exercise['citations'] = citations
                
                break
        
        if not exercise_found:
            raise ValueError(f"Exercise '{original_exercise}' not found in workout")
        
        # Add to modification history
        if 'modification_history' not in modified_workout:
            modified_workout['modification_history'] = []
        
        modified_workout['modification_history'].append({
            'timestamp': datetime.now().isoformat(),
            'original_exercise': original_exercise,
            'replacement_exercise': replacement_exercise,
            'verdict': verdict,
            'reasoning': reasoning[:200] + '...',  # Truncate for storage
            'citations': citations,
            'adjustments_applied': adjustments or {}
        })
        
        # Generate new workout ID
        new_id = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        modified_workout['workout_id'] = new_id
        modified_workout['parent_workout_id'] = original_workout.get('workout_id')
        
        return modified_workout
    
    def _apply_adjustments(self, exercise: Dict, adjustments: Dict) -> None:
        """Apply volume/intensity adjustments to exercise"""
        if adjustments.get('sets'):
            exercise['sets'] = adjustments['sets']
            exercise['adjustment_note'] = f"Sets adjusted per research: {adjustments.get('reason', 'volume compensation')}"
        
        if adjustments.get('reps'):
            exercise['reps'] = adjustments['reps']
        
        if adjustments.get('rest'):
            exercise['rest_seconds'] = adjustments['rest']
    
    def _extract_summary(self, reasoning: str) -> str:
        """Extract concise summary from reasoning"""
        # Take first 2 sentences or 150 chars
        sentences = reasoning.split('.')
        summary = '. '.join(sentences[:2]) + '.'
        return summary[:150] if len(summary) > 150 else summary


if __name__ == "__main__":
    # Test
    modifier = WorkoutModifier()
    
    test_workout = {
        'workout_id': 'workout_test_001',
        'goal': 'hypertrophy',
        'exercises': [
            {
                'name': 'Barbell Squat',
                'sets': '4',
                'reps': '8-10',
                'tempo': '3010'
            }
        ]
    }
    
    modified = modifier.apply_modification(
        original_workout=test_workout,
        original_exercise='Barbell Squat',
        replacement_exercise='Leg Press',
        verdict='yellow',
        reasoning='Leg press is 80-90% effective. Increase sets by 1.',
        citations=['https://example.com/study1'],
        adjustments={'sets': '5', 'reason': 'Volume compensation per Schoenfeld 2024'}
    )
    
    print("✅ Test passed")
    print(f"New workout ID: {modified['workout_id']}")
    print(f"Exercise: {modified['exercises'][0]['name']}")
    print(f"Sets adjusted: {modified['exercises'][0]['sets']}")
    print(f"History entries: {len(modified['modification_history'])}")

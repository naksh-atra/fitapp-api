"""
Workout modifier v2.0 - applies validated exercise substitutions.

Works with the new weekly_plan structure: searches across all days
to find the target exercise, modifies it in place, and returns the
updated full weekly plan with a new workout_id and modification history.
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
        Apply validated modification to the weekly plan.
        Searches all days → all exercises (including circuit stations).
        Returns modified workout with updated workout_id and history entry.
        """
        modified_workout = copy.deepcopy(original_workout)

        exercise_found = False

        for day_key, day_data in modified_workout.get("weekly_plan", {}).items():
            if exercise_found:
                break
            for item in day_data.get("exercises", []):
                # ── Direct exercise (hypertrophy / strength) ──────────────
                if item.get("name", "").lower() == original_exercise.lower():
                    self._patch_exercise(
                        item, replacement_exercise, verdict,
                        reasoning, citations, adjustments
                    )
                    exercise_found = True
                    break

                # ── Circuit / HIIT station ────────────────────────────────
                for station in item.get("stations", []):
                    station_name = station.get("name") or station.get("exercise") or ""
                    if station_name.lower() == original_exercise.lower():
                        # Normalise station to always use 'name' key
                        if "exercise" in station and "name" not in station:
                            station["name"] = station.pop("exercise")
                        self._patch_exercise(
                            station, replacement_exercise, verdict,
                            reasoning, citations, adjustments
                        )
                        exercise_found = True
                        break

                if exercise_found:
                    break

        if not exercise_found:
            raise ValueError(
                f"Exercise '{original_exercise}' not found in any session of the weekly plan."
            )

        # ── Modification history ──────────────────────────────────────────
        if "modification_history" not in modified_workout:
            modified_workout["modification_history"] = []

        modified_workout["modification_history"].append({
            "timestamp":            datetime.now().isoformat(),
            "original_exercise":    original_exercise,
            "replacement_exercise": replacement_exercise,
            "verdict":              verdict,
            "reasoning":            (reasoning[:200] + "...") if len(reasoning) > 200 else reasoning,
            "citations":            citations,
            "adjustments_applied":  adjustments or {},
        })

        # ── New workout ID ────────────────────────────────────────────────
        modified_workout["parent_workout_id"] = original_workout.get("workout_id")
        modified_workout["workout_id"]        = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return modified_workout

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    def _patch_exercise(
        self,
        exercise: Dict,
        replacement_name: str,
        verdict: str,
        reasoning: str,
        citations: list,
        adjustments: Optional[Dict]
    ) -> None:
        """Mutate an exercise dict in place with the replacement details."""
        exercise["original_name"]      = exercise.get("name") or exercise.get("exercise")
        exercise["name"]               = replacement_name
        exercise["modified"]           = True
        exercise["modification_note"]  = self._extract_summary(reasoning)
        exercise["citations"]          = citations

        # Apply volume/intensity adjustments on YELLOW verdict
        if verdict.lower() == "yellow" and adjustments:
            self._apply_adjustments(exercise, adjustments)

    def _apply_adjustments(self, exercise: Dict, adjustments: Dict) -> None:
        if adjustments.get("sets"):
            exercise["sets"]            = adjustments["sets"]
            exercise["adjustment_note"] = f"Sets adjusted per research: {adjustments.get('reason', 'volume compensation')}"
        if adjustments.get("reps"):
            exercise["reps"] = adjustments["reps"]
        if adjustments.get("rest"):
            exercise["rest_seconds"] = adjustments["rest"]

    def _extract_summary(self, reasoning: str) -> str:
        sentences = reasoning.split(".")
        summary   = ". ".join(sentences[:2]) + "."
        return summary[:150] if len(summary) > 150 else summary


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    modifier = WorkoutModifier()

    test_workout = {
        "workout_id": "workout_test_001",
        "goal": "hypertrophy",
        "weekly_plan": {
            "monday": {
                "session_name": "Push A",
                "session_type": "push",
                "exercises": [
                    {"name": "Barbell Bench Press", "sets": [3, 4], "reps": [6, 8], "tempo": "3010"},
                    {"name": "Overhead Press",      "sets": [3, 4], "reps": [6, 8], "tempo": "3010"},
                ]
            },
            "tuesday": {
                "session_name": "Active Recovery",
                "session_type": "rest",
                "exercises": []
            }
        }
    }

    modified = modifier.apply_modification(
        original_workout=test_workout,
        original_exercise="Barbell Bench Press",
        replacement_exercise="Dumbbell Bench Press",
        verdict="yellow",
        reasoning="Dumbbell bench press is ~90% effective. Increase sets by 1 for volume compensation.",
        citations=["https://example.com/study1"],
        adjustments={"sets": [4, 5], "reason": "Volume compensation per Schoenfeld 2024"}
    )

    print("WorkoutModifier v2.0 test passed")
    print(f"New workout ID : {modified['workout_id']}")
    print(f"Parent ID      : {modified['parent_workout_id']}")
    monday_ex = modified["weekly_plan"]["monday"]["exercises"]
    print(f"Exercise name  : {monday_ex[0]['name']}")
    print(f"Sets adjusted  : {monday_ex[0]['sets']}")
    print(f"History entries: {len(modified['modification_history'])}")

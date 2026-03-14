"""
API Client for FitApp backend
"""

import requests
from typing import Dict, Optional


class FitAppAPI:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", token: Optional[str] = None):
        self.base_url = base_url
        self.token = token

    def _get_headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def generate_workout(
        self,
        goal: str,
        equipment: str = "gym",
        experience: str = "intermediate",
        week: int = 1
    ) -> Dict:
        """Generate workout from API"""
        response = requests.post(
            f"{self.base_url}/generate_workout",
            json={
                "goal": goal,
                "equipment": equipment,
                "experience": experience,
                "week": week
            },
            headers=self._get_headers(),
            timeout=45
        )
        response.raise_for_status()
        return response.json()

    def validate_modification(
        self,
        workout_id: str,
        original_exercise: str,
        replacement_exercise: str,
        reason: str,
        goal: str
    ) -> Dict:
        """Validate exercise substitution"""
        response = requests.post(
            f"{self.base_url}/validate_modification",
            json={
                "workout_id": workout_id,
                "original_exercise": original_exercise,
                "replacement_exercise": replacement_exercise,
                "reason": reason,
                "goal": goal
            },
            headers=self._get_headers(),
            timeout=30  # Perplexity API can be slow
        )
        response.raise_for_status()
        return response.json()

    def apply_modification(
        self,
        workout_id: str,
        modification_id: str,
        original_exercise: str,
        replacement_exercise: str,
        verdict: str,
        reasoning: str,
        citations: list,
        adjustments: Optional[Dict] = None
    ) -> Dict:
        """Apply validated modification"""
        response = requests.post(
            f"{self.base_url}/apply_modification",
            json={
                "workout_id": workout_id,
                "modification_id": modification_id,
                "original_exercise": original_exercise,
                "replacement_exercise": replacement_exercise,
                "verdict": verdict,
                "reasoning": reasoning,
                "citations": citations,
                "adjustments": adjustments
            },
            headers=self._get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json()



#streamlit run src/streamlit_app/app.py --server.port 8501
#python src/api/main.py
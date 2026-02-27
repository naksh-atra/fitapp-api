# src/validation/research_validator.py
import os
import requests
from typing import Dict, Literal


class ResearchValidator:

    SUBSTITUTION_CONTEXT = {
        "strength": "GREEN = similar 1RM loading potential and motor pattern. YELLOW = slight load reduction but same pattern. RED = fundamentally different pattern or significant load reduction.",
        "endurance": "GREEN = similar metabolic demand and rep tolerance at high reps. YELLOW = slightly lower endurance capacity. RED = exercise that limits reps or raises injury risk at high rep ranges.",
        "fatloss": "GREEN = similar caloric expenditure and heart rate elevation. YELLOW = lower metabolic output but acceptable. RED = low-intensity isolation that significantly reduces metabolic output.",
        "hypertrophy": "GREEN = similar muscle recruitment and volume capacity. YELLOW = 70-90% effective. RED = significant reduction in stimulus to target muscle."
    }

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = os.getenv("MODEL")

    def validate_exercise_swap(
        self,
        original: str,
        replacement: str,
        reason: str,
        goal: str = "hypertrophy"
    ) -> Dict:
        """
        Query Perplexity API to validate exercise substitution.
        Returns verdict (GREEN/YELLOW/RED) with research backing.
        """

        prompt = self._build_validation_prompt(original, replacement, reason, goal)

        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research validator for exercise prescription. Evaluate exercise substitutions based on peer-reviewed evidence from 2023-2025. Return verdicts as GREEN (equivalent/valid), YELLOW (suboptimal but acceptable), or RED (not recommended)."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,  # Low temp for consistency
                "return_citations": True,
                "search_recency_filter": "year"  # Only recent research
            }
        )

        return self._parse_api_response(response.json())

    def _build_validation_prompt(self, original, replacement, reason, goal):
        goal_context = self.SUBSTITUTION_CONTEXT.get(goal, self.SUBSTITUTION_CONTEXT["hypertrophy"])
        return f"""
        Evaluate this exercise substitution for {goal}:

        ORIGINAL: {original}
        PROPOSED REPLACEMENT: {replacement}
        REASON: {reason}

        Analyze:
        1. Muscle activation comparison (primary & secondary muscles)
        2. Biomechanical equivalence
        3. Effectiveness for {goal} (cite specific studies from 2023-2025)
        4. Safety considerations for reason: {reason}
        5. Required adjustments (sets/reps/tempo) if accepted

        Return verdict as:
        - GREEN if equivalent or superior
        - YELLOW if 70-90% as effective with adjustments
        - RED if <70% effective or unsafe

        Verdict criteria for {goal}: {goal_context}

        Include specific study citations and effectiveness percentage.
        """

    def _parse_api_response(self, response_data: Dict) -> Dict:
        """
        Parse Perplexity API response into structured verdict.
        Verdict is returned in lowercase (green / yellow / red) so the
        existing /validate_modification endpoint and Streamlit page work
        without any changes.  The /validate_swap endpoint uppercases at
        its own boundary for test compatibility.
        """
        content = response_data['choices'][0]['message']['content']
        citations = response_data.get('citations', [])

        # Detect verdict (case-insensitive search, return lowercase)
        content_upper = content.upper()
        if "GREEN" in content_upper:
            verdict = "green"
        elif "YELLOW" in content_upper:
            verdict = "yellow"
        elif "RED" in content_upper:
            verdict = "red"
        else:
            verdict = "yellow"  # Default to caution

        return {
            "verdict": verdict,
            "reasoning": content,
            "citations": citations,
            "timestamp": response_data.get('created')
        }


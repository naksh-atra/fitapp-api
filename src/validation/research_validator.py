# src/validation/research_validator.py
import os
import requests
import re
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
        self.model = os.getenv("MODEL", "sonar") # Use 'sonar' as standard online model

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
        system_instructions = "You are a research validator for exercise prescription. Evaluate exercise substitutions based on peer-reviewed evidence from 2023-2025. Return verdicts as GREEN (equivalent/valid), YELLOW (suboptimal but acceptable), or RED (not recommended)."

        # Try standard approach
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self._call_perplexity_api(messages)
            
            # If 400 because of 'system' role, retry with merged user message
            if response.status_code == 400 and "system" in response.text.lower():
                print("⚠️ Retrying without system role...")
                merged_prompt = f"{system_instructions}\n\n{prompt}"
                response = self._call_perplexity_api([{"role": "user", "content": merged_prompt}])

            print(f"DEBUG: Perplexity API Status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Perplexity API ERROR DETAIL: {response.text}")
                return self._error_fallback(f"API Error ({response.status_code}): {response.text}")

            return self._parse_api_response(response.json())

        except Exception as e:
            print(f"❌ Research Validator Crash: {e}")
            return self._error_fallback(str(e))

    def _call_perplexity_api(self, messages):
        return requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ResFit-Research-Engine/1.0"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "return_citations": True
            },
            timeout=60
        )

    def _error_fallback(self, error_str: str) -> Dict:
        return {
            "verdict": "red",
            "corrected_name": None,
            "reasoning": f"Validation system Error: {error_str}",
            "citations": [],
            "timestamp": None
        }

    def _build_validation_prompt(self, original, replacement, reason, goal):
        goal_context = self.SUBSTITUTION_CONTEXT.get(goal, self.SUBSTITUTION_CONTEXT["hypertrophy"])
        return f"""
        Evaluate or suggest an exercise substitution for {goal}:
        
        ORIGINAL: {original}
        PROPOSED REPLACEMENT/CONSTRAINT: {replacement}
        REASON: {reason}

        INSTRUCTION:
        1. Evaluate biomechanical equivalence and effectiveness.
        2. Analyze muscle activation (cite research 2023-2025).
        3. Recommend a CANONICAL NAME if the input is vague.

        Format response:
        CANONICAL NAME: [Name]
        VERDICT: [GREEN/YELLOW/RED]
        PERCENTAGE: [XX]%

        Analysis: [Details...]

        Criteria for {goal}: {goal_context}
        """

    def _parse_api_response(self, response_data: Dict) -> Dict:
        try:
            if 'choices' in response_data:
                content = response_data['choices'][0]['message']['content']
            elif 'output' in response_data:
                content = response_data['output'][0]['message']['content']
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown API Error')
                raise KeyError(f"API Error: {error_msg}")
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ Parse Error: {e} - Data: {response_data}")
            raise Exception(f"Invalid API response: {str(e)}")

        citations = response_data.get('citations', [])
        canonical_match = re.search(r"CANONICAL NAME:\s*(.*)", content, re.IGNORECASE)
        corrected_name = canonical_match.group(1).strip() if canonical_match else None

        # Detect verdict
        content_upper = content.upper()
        if "GREEN" in content_upper: verdict = "green"
        elif "YELLOW" in content_upper: verdict = "yellow"
        elif "RED" in content_upper: verdict = "red"
        else: verdict = "yellow"

        return {
            "verdict": verdict,
            "corrected_name": corrected_name,
            "reasoning": content,
            "citations": citations,
            "timestamp": response_data.get('created')
        }

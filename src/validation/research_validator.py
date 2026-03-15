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
        self.model = os.getenv("MODEL", "sonar-reasoning")  # Default if env var missing

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
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ResFit-Research-Engine/1.0"
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
                "temperature": 0.2,
                "return_citations": True
            },
            timeout=60  # Perplexity research can take time
        )
        
        response.raise_for_status()

        print(f"DEBUG: Perplexity API Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Perplexity API Error: {response.text}")
            return {
                "verdict": "red",
                "corrected_name": None,
                "reasoning": f"Research API Error ({response.status_code}): {response.text}",
                "citations": [],
                "timestamp": None
            }
            
        return self._parse_api_response(response.json())

    def _build_validation_prompt(self, original, replacement, reason, goal):
        goal_context = self.SUBSTITUTION_CONTEXT.get(goal, self.SUBSTITUTION_CONTEXT["hypertrophy"])
        return f"""
        Evaluate or suggest an exercise substitution for {goal}:
        
        ORIGINAL: {original}
        PROPOSED REPLACEMENT/CONSTRAINT: {replacement}
        REASON: {reason}

        INSTRUCTION:
        1. If the PROPOSED REPLACEMENT is a specific exercise, evaluate its biomechanical equivalence and effectiveness.
        2. If the PROPOSED REPLACEMENT is a constraint (e.g., 'no kettlebells', 'something at home', 'easier version') or is vague, use your research knowledge to SUGGEST the single best Canonical Replacement that aligns with the original goal and honors the constraint.

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

        Format your response exactly as follows at the VERY START:
        CANONICAL NAME: [Exact Name of Suggested Replacement Exercise]
        VERDICT: [GREEN/YELLOW/RED]
        PERCENTAGE: [XX]%

        Then provide detailed analysis and citations.
        
        Verdict criteria for {goal}: {goal_context}
        """

    def _parse_api_response(self, response_data: Dict) -> Dict:
        """
        Parse Perplexity API response into structured verdict.
        Verdict is returned in lowercase (green / yellow / red) so the
        existing /validate_modification endpoint and Streamlit page work
        without any changes.  The /validate_swap endpoint uppercases at
        its own boundary for test compatibility.
        """
        try:
            # Flexible parsing: Check 'choices' (Standard) or 'output' (Some Perplexity models)
            if 'choices' in response_data:
                content = response_data['choices'][0]['message']['content']
            elif 'output' in response_data:
                content = response_data['output'][0]['message']['content']
            else:
                # If neither is found, it's likely an error message
                error_msg = response_data.get('error', {}).get('message', 'Unknown API Error')
                raise KeyError(f"API Error/Missing Content: {error_msg}")
        except (KeyError, IndexError, TypeError) as e:
            print(f"❌ Failed to parse Perplexity response! {e}")
            print(f"Raw Response: {response_data}")
            raise Exception(f"Invalid research API response structure: {str(e)}")
        citations = response_data.get('citations', [])

        # Extract Canonical Name
        canonical_match = re.search(r"CANONICAL NAME:\s*(.*)", content, re.IGNORECASE)
        corrected_name = canonical_match.group(1).strip() if canonical_match else None

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
            "corrected_name": corrected_name,
            "reasoning": content,
            "citations": citations,
            "timestamp": response_data.get('created')
        }


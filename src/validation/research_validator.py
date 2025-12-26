# src/validation/research_validator.py
import os
import requests
from typing import Dict, Literal

class ResearchValidator:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
    def validate_exercise_swap(
        self,
        original: str,
        replacement: str,
        reason: str,
        goal: str = "hypertrophy"
    ) -> Dict:
        """
        Query Perplexity API to validate exercise substitution.
        Returns verdict (green/yellow/red) with research backing.
        """
        
        prompt = self._build_validation_prompt(original, replacement, reason, goal)
        
        response = requests.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",  # Use Pro model for research quality
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
        
        Include specific study citations and effectiveness percentage.
        """
    
    def _parse_api_response(self, response_data: Dict) -> Dict:
        """
        Parse Perplexity API response into structured verdict.
        """
        content = response_data['choices'][0]['message']['content']
        citations = response_data.get('citations', [])
        
        # Simple parsing logic - you'll refine this
        if "GREEN" in content.upper():
            verdict = "green"
        elif "YELLOW" in content.upper():
            verdict = "yellow"
        elif "RED" in content.upper():
            verdict = "red"
        else:
            verdict = "yellow"  # Default to caution
        
        return {
            "verdict": verdict,
            "reasoning": content,
            "citations": citations,
            "timestamp": response_data.get('created')
        }

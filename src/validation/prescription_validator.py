"""
Prescription Validator
Validates entire workout prescriptions using research
"""

import os
import requests
from typing import Dict, List
import json
from datetime import datetime


class PrescriptionValidator:
    """Validate workout prescriptions against research"""
    
    def __init__(self, cache_path: str = "data/validation_cache/prescription_cache.json"):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.cache_path = cache_path
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cached validations"""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Cache load error: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def validate_prescription(
        self,
        goal: str,
        exercises: List[Dict],
        equipment: str = "gym",
        experience: str = "intermediate"
    ) -> Dict:
        """
        Validate an entire workout prescription
        Returns: {
            "validated": True,
            "evidence_summary": "...",
            "citations": [...],
            "confidence": "high"
        }
        """
        
        # Create cache key
        cache_key = f"{goal}_{equipment}_{experience}"
        
        # Check cache first
        if cache_key in self.cache:
            print(f"✓ Using cached validation for {goal}")
            return self.cache[cache_key]
        
        # Build research query
        query = self._build_validation_query(goal, exercises, equipment, experience)
        
        # Query Perplexity
        print(f"🔬 Validating {goal} prescription with research...")
        result = self._query_perplexity(query)
        
        # Parse response
        validation_result = self._parse_validation_response(result, goal)
        
        # Cache result
        self.cache[cache_key] = validation_result
        self._save_cache()
        
        return validation_result
    
    def _build_validation_query(
        self,
        goal: str,
        exercises: List[Dict],
        equipment: str,
        experience: str
    ) -> str:
        """Build research query for prescription validation"""
        
        # Summarize exercises
        exercise_summary = []
        for ex in exercises[:6]:  # First 6 exercises
            name = ex['name']
            sets = ex['sets']
            reps = ex['reps']
            
            if isinstance(sets, list):
                sets_str = f"{sets[0]}-{sets[1]}"
            else:
                sets_str = str(sets)
            
            if isinstance(reps, list):
                reps_str = f"{reps[0]}-{reps[1]}"
            else:
                reps_str = str(reps)
            
            exercise_summary.append(f"{name} ({sets_str} sets, {reps_str} reps)")
        
        exercises_text = "\n- ".join(exercise_summary)
        
        query = f"""
I need to validate a {goal} workout prescription for {experience} trainees using {equipment} equipment.

The prescription includes:
- {exercises_text}

Based on recent research (2023-2025), please:

1. Confirm if this prescription aligns with current evidence for {goal}
2. Validate the set/rep ranges for {goal} training
3. Assess if exercise selection is optimal for {goal}
4. Provide 3-5 key research citations supporting this approach

Focus on:
- Recent meta-analyses or systematic reviews (2023-2025)
- Studies on {goal} training protocols
- Evidence on volume, intensity, and exercise selection

Provide citations with full URLs.
"""
        
        return query.strip()
    
    def _query_perplexity(self, query: str) -> str:
        """Query Perplexity API"""
        
        if not self.api_key:
            return "Error: PERPLEXITY_API_KEY not set"
        
        payload = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a sports science researcher analyzing workout prescriptions. Provide evidence-based analysis with recent citations (2023-2025). Always include full citation URLs."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        
        except Exception as e:
            print(f"Perplexity API error: {e}")
            return f"Error: {str(e)}"
    
    def _parse_validation_response(self, response: str, goal: str) -> Dict:
        """Parse Perplexity response into structured format"""
        
        # Extract citations (URLs)
        import re
        url_pattern = r'https?://[^\s\)]+'
        citations = list(set(re.findall(url_pattern, response)))
        
        # Determine confidence based on response
        confidence = "high"  # Default
        if "not optimal" in response.lower() or "limited evidence" in response.lower():
            confidence = "medium"
        if "insufficient" in response.lower() or "no evidence" in response.lower():
            confidence = "low"
        
        return {
            "validated": True,
            "goal": goal,
            "evidence_summary": response,
            "citations": citations[:8],  # Limit to 8 citations
            "confidence": confidence,
            "validated_at": datetime.now().isoformat(),
            "source": "perplexity_api"
        }

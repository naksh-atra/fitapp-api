# """
# Prescription Validator
# Validates entire workout prescriptions using research
# """

# import os
# import requests
# from typing import Dict, List
# import json
# from datetime import datetime
# #extract urls
# import re


# class PrescriptionValidator:
#     """Validate workout prescriptions against research"""

#     GOAL_CONTEXT = {
#         "strength": {
#             "focus": "maximal strength (1RM improvement)",
#             "key_variables": "load >80% 1RM, rest 3-5 min, low reps 1-6, compound-dominant",
#             "citation_focus": "strength-specific meta-analyses, powerlifting RCTs, 1RM studies 2023-2025"
#         },
#         "endurance": {
#             "focus": "muscular endurance and aerobic capacity",
#             "key_variables": "high reps 15-30, short rest 20-60s, load <60% 1RM, circuit density",
#             "citation_focus": "endurance-RT interaction, ACSM guidelines, circuit training meta-analyses 2023-2025"
#         },
#         "fatloss": {
#             "focus": "fat mass reduction while preserving lean mass",
#             "key_variables": "metabolic stress, HIIT-RT combination, moderate load moderate rep, short rest",
#             "citation_focus": "body composition RCTs, HIIT+RT combination studies 2023-2025"
#         },
#         "hypertrophy": {
#             "focus": "muscle hypertrophy",
#             "key_variables": "volume 10-20 sets/muscle/week, reps 6-20, proximity to failure",
#             "citation_focus": "hypertrophy meta-analyses, volume-response studies 2023-2025"
#         }
#     }

#     #constructor to read api key from env, set api endpoints, set cached data location, also loads existing cache
#     def __init__(self, cache_path: str = "data/validation_cache/prescription_cache.json"):
#         self.api_key = os.getenv("PERPLEXITY_API_KEY")
#         self.api_url = "https://api.perplexity.ai/chat/completions"
#         self.model = os.getenv("MODEL")
#         self.cache_path = cache_path
#         self.cache = self._load_cache()
        
#         # DEBUG: Show what key we're actually using
#         print(f"[PrescriptionValidator] API Key prefix: {self.api_key[:12] if self.api_key else 'MISSING'}")
    
#     def _load_cache(self) -> Dict:
#         """Load cached validations"""
#         try:
#             if os.path.exists(self.cache_path):
#                 with open(self.cache_path, 'r') as f:
#                     return json.load(f)
#         except Exception as e:
#             print(f"Cache load error: {e}")
#         return {}
    
#     def _save_cache(self):
#         """Save cache to disk"""
#         try:
#             os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
#             with open(self.cache_path, 'w') as f:
#                 json.dump(self.cache, f, indent=2)
#         except Exception as e:
#             print(f"Cache save error: {e}")
    
#     def validate_prescription(self, goal: str, exercises: List[Dict], equipment: str = "gym", experience: str = "intermediate") -> Dict:
#         """
#         Validate an entire workout prescription
#         Returns: {
#             "validated": True,
#             "evidence_summary": "...",
#             "citations": [...],
#             "confidence": "high"
#         }
#         """
        
#         # Cache key: goal + equipment + experience only.
#         # Do NOT include exercise names — the validator checks the prescription
#         # approach, not the specific exercises, and exercise names change when
#         # generators are updated (which would bust the cache unnecessarily).
#         cache_key = f"{goal}_{equipment}_{experience}"
        
#         print(f"🔥 Cache key: {cache_key}")  # DEBUG
        
#         # Check cache first
#         if cache_key in self.cache:
#             print(f"✓ Using cached validation for {goal}")
#             return self.cache[cache_key]
        
#         # Build research query
#         query = self._build_validation_query(goal, exercises, equipment, experience)
        
#         # Query Perplexity
#         print(f"🔬 Validating {goal} prescription with research...")
#         perplexity_result = self._query_perplexity(query, goal)  # Pass goal here
        
#         # Parse response - handles both success dict and error string
#         validation_result = self._parse_validation_response(perplexity_result, goal)

#         # Only cache successful responses 
#         if validation_result.get('validated', False) and not validation_result['evidence_summary'].startswith('Error:'):
#             self.cache[cache_key] = validation_result
#             self._save_cache()
#         else:
#             print(f"NOT caching error response for {goal}")
        
#         return validation_result
    
#     def _build_validation_query(
#         self,
#         goal: str,
#         exercises: List[Dict],
#         equipment: str,
#         experience: str
#     ) -> str:
#         """Build goal-aware research query for prescription validation"""

#         ctx = self.GOAL_CONTEXT.get(goal, self.GOAL_CONTEXT["hypertrophy"])

#         # Summarize exercises
#         exercise_summary = []
#         for ex in exercises[:6]:  # First 6 exercises
#             name = ex['name']
#             sets = ex.get('sets', '?')
#             reps = ex.get('reps', '?')

#             if isinstance(sets, list):
#                 sets_str = f"{sets[0]}-{sets[1]}"
#             else:
#                 sets_str = str(sets)

#             if isinstance(reps, list):
#                 reps_str = f"{reps[0]}-{reps[1]}"
#             else:
#                 reps_str = str(reps)

#             exercise_summary.append(f"{name} ({sets_str} sets, {reps_str} reps)")

#         exercises_text = "\n- ".join(exercise_summary)

#         query = f"""
# Validate a {goal} workout for {experience} trainees using {equipment}.

# Goal focus: {ctx['focus']}
# Key variables to validate: {ctx['key_variables']}

# Prescription:
# - {exercises_text}

# Validate against 2023-2025 research:
# 1. Does this align with {goal} evidence?
# 2. Are sets/reps/rest optimal for {ctx['focus']}?
# 3. Is exercise selection appropriate?
# 4. Provide 3-5 citations from: {ctx['citation_focus']}

# Include full citation URLs.
# """
#         return query.strip()
    
#     def _query_perplexity(self, query: str, goal: str) -> dict:
#         """Query Perplexity API - ALWAYS returns a dict, never raises exceptions"""
        
#         if not self.api_key:
#             return {"error": "No API key configured", "status_code": 500}
    
#         payload = {
#             "model": self.model,
#             "messages": [
#                 {"role": "system", "content": "You are a sports science researcher analyzing workout prescriptions. Provide evidence-based analysis with recent citations (2023-2025). Always include full citation URLs."},
#                 {"role": "user", "content": f"Goal: {goal}\nPrescription: {query}"}
#             ],
#             "temperature": 0.1,
#             "max_tokens": 1000
#         }
    
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
        
#         # DEBUG: Print everything Perplexity sees
#         print("🔍 DEBUG PAYLOAD:")
#         print(f"  Model: {payload['model']}")
#         print(f"  Messages count: {len(payload['messages'])}")
#         print(f"  Temperature: {payload['temperature']}")
#         print(f"  API Key prefix: {self.api_key[:12] if self.api_key else 'MISSING'}")
#         print(f"  Full payload size: {len(json.dumps(payload))} chars")
#         print()
        
#         try:
#             response = requests.post(
#                 self.api_url,
#                 json=payload,
#                 headers=headers,
#                 timeout=25   # 25s so we fail before the client's 30s budget
#             )
            
#             print(f"RAW PERPLEXITY RESPONSE ({response.status_code}): {response.text[:200]}...")
            
#             # NEVER raise_for_status() - handle all status codes
#             if response.status_code != 200:
#                 return {
#                     "error": f"HTTP {response.status_code}: {response.text[:100]}",
#                     "status_code": response.status_code
#                 }
            
#             result = response.json()
            
#             if "choices" not in result or not result["choices"]:
#                 return {"error": "Invalid response structure (no choices)", "status_code": 502}
            
#             raw_content = result['choices'][0]['message']['content']
            
#             print(f"\n🔍 RAW CONTENT ({len(raw_content)} chars):")
#             print("-" * 80)
#             print(raw_content[:800])  # First 800 chars
#             print("-" * 80)
#             print("URLs found: " + str(re.findall(r'https?://[^\s\)]+', raw_content)))
#             print()
            
#             return {"success": True, "content": raw_content}
            
#         except requests.exceptions.RequestException as e:
#             print(f"Network error: {e}")
#             return {"error": f"Network error: {str(e)}", "status_code": 502}
#         except Exception as e:
#             print(f"Unexpected error: {e}")
#             return {"error": f"Unexpected error: {str(e)}", "status_code": 500}
    
#     def _parse_validation_response(self, response: dict, goal: str) -> Dict:
#         """Parse Perplexity response into structured format - handles both success and error"""
        
#         # Handle error case first
#         if "error" in response:
#             return {
#                 "validated": False,
#                 "goal": goal,
#                 "evidence_summary": f"Research validation unavailable: {response['error']}",
#                 "citations": [],
#                 "confidence": "unknown",
#                 "validated_at": datetime.now().isoformat(),
#                 "source": f"perplexity_{response.get('status_code', 500)}"
#             }
        
#         # Success case
#         raw_response = response["content"]
#         url_pattern = r'https?://[^\s\)]+'
#         all_urls = re.findall(url_pattern, raw_response)
        
#         # Filter out API endpoints and invalid URLs
#         citations = [
#             url for url in set(all_urls)
#             if not any(exclude in url.lower() for exclude in [
#                 'api.perplexity.ai',
#                 'localhost',
#                 '127.0.0.1',
#                 'example.com',
#                 'streamlit.io',
#                 'ngrok.io',
#             ])
#         ]
        
#         # Determine confidence based on response
#         confidence = "high"  # Default
#         if "not optimal" in raw_response.lower() or "limited evidence" in raw_response.lower():
#             confidence = "medium"
#         if "insufficient" in raw_response.lower() or "no evidence" in raw_response.lower():
#             confidence = "low"
        
#         return {
#             "validated": True,
#             "goal": goal,
#             "evidence_summary": raw_response,
#             "citations": citations[:8] if citations else ['No direct citations available - see evidence summary'],  # Limit to 8 citations
#             "confidence": confidence,
#             "validated_at": datetime.now().isoformat(),
#             "source": "perplexity_api"
#         }



"""
Prescription Validator
Validates entire workout prescriptions using research
"""

import os
import requests
from typing import Dict, List
import json
from datetime import datetime
import re

from repositories import get_cached_validation, save_cached_validation   # NEW


class PrescriptionValidator:
    """Validate workout prescriptions against research"""

    GOAL_CONTEXT = {
        "strength": {
            "focus": "maximal strength (1RM improvement)",
            "key_variables": "load >80% 1RM, rest 3-5 min, low reps 1-6, compound-dominant",
            "citation_focus": "strength-specific meta-analyses, powerlifting RCTs, 1RM studies 2023-2025"
        },
        "endurance": {
            "focus": "muscular endurance and aerobic capacity",
            "key_variables": "high reps 15-30, short rest 20-60s, load <60% 1RM, circuit density",
            "citation_focus": "endurance-RT interaction, ACSM guidelines, circuit training meta-analyses 2023-2025"
        },
        "fatloss": {
            "focus": "fat mass reduction while preserving lean mass",
            "key_variables": "metabolic stress, HIIT-RT combination, moderate load moderate rep, short rest",
            "citation_focus": "body composition RCTs, HIIT+RT combination studies 2023-2025"
        },
        "hypertrophy": {
            "focus": "muscle hypertrophy",
            "key_variables": "volume 10-20 sets/muscle/week, reps 6-20, proximity to failure",
            "citation_focus": "hypertrophy meta-analyses, volume-response studies 2023-2025"
        }
    }

    def __init__(self):                                                    # CHANGED: removed cache_path param
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.model   = os.getenv("MODEL")
        print(f"[PrescriptionValidator] API Key prefix: {self.api_key[:12] if self.api_key else 'MISSING'}")

    # REMOVED: _load_cache()
    # REMOVED: _save_cache()

    def validate_prescription(self, goal: str, exercises: List[Dict], equipment: str = "gym", experience: str = "intermediate") -> Dict:
        """
        Validate an entire workout prescription
        Returns: {
            "validated": True,
            "evidence_summary": "...",
            "citations": [...],
            "confidence": "high"
        }
        """

        cache_key = f"{goal}_{equipment}_{experience}"
        print(f"🔥 Cache key: {cache_key}")

        # Check Mongo cache first                                          # CHANGED
        cached = get_cached_validation(cache_key)                          # CHANGED
        if cached:                                                         # CHANGED
            print(f"✓ Using DB cached validation for {goal}")             # CHANGED
            return cached                                                  # CHANGED

        # Build research query
        query = self._build_validation_query(goal, exercises, equipment, experience)

        # Query Perplexity
        print(f"🔬 Validating {goal} prescription with research...")
        perplexity_result = self._query_perplexity(query, goal)

        # Parse response
        validation_result = self._parse_validation_response(perplexity_result, goal)

        # Only cache successful responses                                  # CHANGED
        if validation_result.get('validated', False) and not validation_result['evidence_summary'].startswith('Error:'):
            meta = {"goal": goal, "equipment": equipment, "experience": experience}
            save_cached_validation(cache_key, meta, validation_result)    # CHANGED
        else:
            print(f"NOT caching error response for {goal}")

        return validation_result

    def _build_validation_query(self, goal: str, exercises: List[Dict], equipment: str, experience: str) -> str:
        """Build goal-aware research query for prescription validation"""

        ctx = self.GOAL_CONTEXT.get(goal, self.GOAL_CONTEXT["hypertrophy"])

        exercise_summary = []
        for ex in exercises[:6]:
            name = ex['name']
            sets = ex.get('sets', '?')
            reps = ex.get('reps', '?')

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
Validate a {goal} workout for {experience} trainees using {equipment}.

Goal focus: {ctx['focus']}
Key variables to validate: {ctx['key_variables']}

Prescription:
- {exercises_text}

Validate against 2023-2025 research:
1. Does this align with {goal} evidence?
2. Are sets/reps/rest optimal for {ctx['focus']}?
3. Is exercise selection appropriate?
4. Provide 3-5 citations from: {ctx['citation_focus']}

Include full citation URLs.
"""
        return query.strip()

    def _query_perplexity(self, query: str, goal: str) -> dict:
        """Query Perplexity API - ALWAYS returns a dict, never raises exceptions"""

        if not self.api_key:
            return {"error": "No API key configured", "status_code": 500}

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a sports science researcher analyzing workout prescriptions. Provide evidence-based analysis with recent citations (2023-2025). Always include full citation URLs."},
                {"role": "user", "content": f"Goal: {goal}\nPrescription: {query}"}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        print("🔍 DEBUG PAYLOAD:")
        print(f"  Model: {payload['model']}")
        print(f"  Messages count: {len(payload['messages'])}")
        print(f"  Temperature: {payload['temperature']}")
        print(f"  API Key prefix: {self.api_key[:12] if self.api_key else 'MISSING'}")
        print(f"  Full payload size: {len(json.dumps(payload))} chars")
        print()

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=25
            )

            print(f"RAW PERPLEXITY RESPONSE ({response.status_code}): {response.text[:200]}...")

            if response.status_code != 200:
                return {
                    "error": f"HTTP {response.status_code}: {response.text[:100]}",
                    "status_code": response.status_code
                }

            result = response.json()

            if "choices" not in result or not result["choices"]:
                return {"error": "Invalid response structure (no choices)", "status_code": 502}

            raw_content = result['choices'][0]['message']['content']

            print(f"\n🔍 RAW CONTENT ({len(raw_content)} chars):")
            print("-" * 80)
            print(raw_content[:800])
            print("-" * 80)
            print("URLs found: " + str(re.findall(r'https?://[^\s\)]+', raw_content)))
            print()

            return {"success": True, "content": raw_content}

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return {"error": f"Network error: {str(e)}", "status_code": 502}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"error": f"Unexpected error: {str(e)}", "status_code": 500}

    def _parse_validation_response(self, response: dict, goal: str) -> Dict:
        """Parse Perplexity response into structured format - handles both success and error"""

        if "error" in response:
            return {
                "validated": False,
                "goal": goal,
                "evidence_summary": f"Research validation unavailable: {response['error']}",
                "citations": [],
                "confidence": "unknown",
                "validated_at": datetime.now().isoformat(),
                "source": f"perplexity_{response.get('status_code', 500)}"
            }

        raw_response = response["content"]
        url_pattern = r'https?://[^\s\)]+'
        all_urls = re.findall(url_pattern, raw_response)

        citations = [
            url for url in set(all_urls)
            if not any(exclude in url.lower() for exclude in [
                'api.perplexity.ai', 'localhost', '127.0.0.1',
                'example.com', 'streamlit.io', 'ngrok.io',
            ])
        ]

        confidence = "high"
        if "not optimal" in raw_response.lower() or "limited evidence" in raw_response.lower():
            confidence = "medium"
        if "insufficient" in raw_response.lower() or "no evidence" in raw_response.lower():
            confidence = "low"

        return {
            "validated": True,
            "goal": goal,
            "evidence_summary": raw_response,
            "citations": citations[:8] if citations else ['No direct citations available - see evidence summary'],
            "confidence": confidence,
            "validated_at": datetime.now().isoformat(),
            "source": "perplexity_api"
        }

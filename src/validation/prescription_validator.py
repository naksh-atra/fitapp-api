import os
import requests
from typing import Dict, List
import json
from datetime import datetime
import re
from tavily import TavilyClient

from repositories import get_cached_validation, save_cached_validation

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

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.model = os.getenv("MODEL", "sonar")
        
        try:
            self.tavily = TavilyClient(api_key=self.tavily_api_key) if self.tavily_api_key else None
        except Exception as e:
            print(f"⚠️  Tavily initialization failed: {e}")
            self.tavily = None
        
        print(f"[PrescriptionValidator] API Keys loaded. Tavily: {'YES' if self.tavily else 'NO'}")

    def validate_prescription(self, goal: str, exercises: List[Dict], equipment: str = "gym", experience: str = "intermediate") -> Dict:
        """Validate an entire workout prescription"""
        cache_key = f"{goal}_{equipment}_{experience}"
        print(f"🔥 Cache key: {cache_key}")

        # Check Mongo cache first
        cached = get_cached_validation(cache_key)
        if cached:
            print(f"✓ Using DB cached validation for {goal}")
            return cached

        # Build research query
        query = self._build_validation_query(goal, exercises, equipment, experience)

        print(f"🔬 Validating {goal} prescription with research...")
        
        # Hybrid RAG: Search (Tavily) -> Synthesize (Perplexity)
        search_context = ""
        if self.tavily:
            print(f"🔍 Searching Tavily for {goal} research...")
            search_context = self._query_tavily(f"evidence for {goal} workout {equipment} {experience} sports science research 2024")

        # Query Perplexity
        perplexity_result = self._query_perplexity(query, goal, context=search_context)

        # Parse response
        validation_result = self._parse_validation_response(perplexity_result, goal)

        # Only cache successful responses
        if validation_result.get('validated', False) and not validation_result['evidence_summary'].startswith('Error:'):
            meta = {"goal": goal, "equipment": equipment, "experience": experience}
            save_cached_validation(cache_key, meta, validation_result)
        
        return validation_result

    def _build_validation_query(self, goal: str, exercises: List[Dict], equipment: str, experience: str) -> str:
        ctx = self.GOAL_CONTEXT.get(goal, self.GOAL_CONTEXT["hypertrophy"])
        exercise_summary = []
        for ex in exercises[:6]:
            name = ex['name']
            sets = ex.get('sets', '?')
            reps = ex.get('reps', '?')
            sets_str = f"{sets[0]}-{sets[1]}" if isinstance(sets, list) else str(sets)
            reps_str = f"{reps[0]}-{reps[1]}" if isinstance(reps, list) else str(reps)
            exercise_summary.append(f"{name} ({sets_str} sets, {reps_str} reps)")

        exercises_text = "\n- ".join(exercise_summary)
        query = f"""Validate a {goal} workout for {experience} trainees using {equipment}.
Goal focus: {ctx['focus']}
Key variables to validate: {ctx['key_variables']}

Prescription:
- {exercises_text}

Validate against 2023-2025 research:
1. Does this align with {goal} evidence?
2. Are sets/reps/rest optimal for {ctx['focus']}?
3. Is exercise selection appropriate?
"""
        return query.strip()

    def _query_tavily(self, query: str) -> str:
        """Search Tavily for raw science snippets"""
        if not self.tavily:
            return ""
        try:
            response = self.tavily.search(query=query, search_depth="advanced", max_results=5)
            return "\n".join([f"[Source: {r['url']}]\n{r['content']}" for r in response.get('results', [])])
        except Exception as e:
            print(f"⚠️  Tavily search error: {e}")
            return ""

    def _query_perplexity(self, query: str, goal: str, context: str = "") -> dict:
        if not self.api_key:
            return {"error": "No API key configured", "status_code": 500}

        if context:
            system_prompt = f"You are a sports science researcher. Answer ONLY using the provided research context below.\n\nRetrieved Research:\n{context}"
            user_content = f"Analyze this {goal} prescription based on the provided research: {query}"
        else:
            system_prompt = "You are a sports science researcher analyzing workout prescriptions. Provide concise evidence-based analysis with recent citations (2023-2025). Always include full citation URLs."
            user_content = f"Goal: {goal}\nPrescription: {query}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        try:
            response = requests.post(self.api_url, json=payload, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, timeout=25)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}", "status_code": response.status_code}
            
            result = response.json()
            raw_content = result['choices'][0]['message']['content']
            api_citations = result.get('citations', [])
            return {"success": True, "content": raw_content, "api_citations": api_citations}
        except Exception as e:
            return {"error": str(e), "status_code": 500}

    def _parse_validation_response(self, response: dict, goal: str) -> Dict:
        if "error" in response:
            return {"validated": False, "goal": goal, "evidence_summary": f"Error: {response['error']}", "citations": [], "confidence": "unknown", "validated_at": datetime.now().isoformat(), "source": "perplexity_error"}

        raw_response = response["content"]
        api_citations = response.get("api_citations", [])
        text_urls = re.findall(r'https?://[^\s\)]+', raw_response)
        combined_urls = list(set(api_citations + text_urls))
        
        citations = [u for u in combined_urls if not any(x in u.lower() for x in ['api.perplexity.ai', 'localhost', '127.0.0.1', 'example.com', 'streamlit.io'])]

        text = raw_response.lower()
        confidence = "medium"
        if any(kw in text for kw in ["strongly supported", "aligns with", "highly effective", "optimal"]): confidence = "high"
        if any(kw in text for kw in ["insufficient evidence", "no scientific evidence", "unsafe"]): confidence = "low"

        return {
            "validated": True,
            "goal": goal,
            "evidence_summary": raw_response,
            "citations": citations[:8] if citations else ['No direct citations available'],
            "confidence": confidence,
            "validated_at": datetime.now().isoformat(),
            "source": "perplexity_api"
        }

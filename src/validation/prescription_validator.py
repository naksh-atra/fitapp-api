import os
import re
from typing import Dict, List
from datetime import datetime
from tavily import TavilyClient

from repositories import get_cached_validation, save_cached_validation
from utils import LLMClient, QueryTransformer


ACADEMIC_DOMAINS = [
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "journals.lww.com",
    "sciencedirect.com",
    "nih.gov",
    "tandfonline.com",
    "mdpi.com",
    "bjsm.bmj.com",
    "acsm.org",
    "nsca.com",
    "scholar.google.com",
    "scopus.com",
    "webofscience.com"
]


class PrescriptionValidator:
    """Validate workout prescriptions using Tavily + LLM (OpenRouter)"""

    GOAL_CONTEXT = {
        "strength": {
            "focus": "maximal strength (1RM improvement)",
            "key_variables": "load >80% 1RM, rest 3-5 min, low reps 1-6, compound-dominant",
            "citation_focus": "strength-specific meta-analyses, powerlifting RCTs, 1RM studies 2020-2026"
        },
        "endurance": {
            "focus": "muscular endurance and aerobic capacity",
            "key_variables": "high reps 15-30, short rest 20-60s, load <60% 1RM, circuit density",
            "citation_focus": "endurance-RT interaction, ACSM guidelines, circuit training meta-analyses 2020-2026"
        },
        "fatloss": {
            "focus": "fat mass reduction while preserving lean mass",
            "key_variables": "metabolic stress, HIIT-RT combination, moderate load moderate rep, short rest",
            "citation_focus": "body composition RCTs, HIIT+RT combination studies 2020-2026"
        },
        "hypertrophy": {
            "focus": "muscle hypertrophy",
            "key_variables": "volume 10-20 sets/muscle/week, reps 6-20, proximity to failure",
            "citation_focus": "hypertrophy meta-analyses, volume-response studies 2020-2026"
        }
    }

    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.llm = LLMClient()
        self.query_transformer = QueryTransformer(self.llm)

        try:
            self.tavily = TavilyClient(api_key=self.tavily_api_key) if self.tavily_api_key else None
        except Exception as e:
            print(f"⚠️  Tavily initialization failed: {e}")
            self.tavily = None

        print(f"[PrescriptionValidator] Tavily: {'YES' if self.tavily else 'NO'}, LLM: {'YES' if self.llm.api_key else 'NO'}")

    def validate_prescription(self, goal: str, exercises: List[Dict], equipment: str = "gym", experience: str = "intermediate") -> Dict:
        """Validate an entire workout prescription using Tavily + OpenRouter"""
        cache_key = f"{goal}_{equipment}_{experience}"
        print(f"🔥 Cache key: {cache_key}")

        cached = get_cached_validation(cache_key)
        if cached:
            print(f"✓ Using DB cached validation for {goal}")
            return cached

        query = self._build_validation_query(goal, exercises, equipment, experience)

        print(f"🔬 Validating {goal} prescription with research...")

        search_context = ""
        citations = []
        if self.tavily:
            search_query = self.query_transformer.transform(
                query=f"evidence for {goal} workout {equipment} {experience} sports science",
                goal=goal
            )
            print(f"🔍 Searching Tavily for {goal} research...")
            search_results = self._query_tavily(search_query)
            search_context = search_results.get("context", "")
            citations = search_results.get("citations", [])

        llm_result = self._query_llm(query, goal, context=search_context)

        validation_result = self._parse_llm_response(llm_result, goal, citations)

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

Validate against 2020-2026 research:
1. Does this align with {goal} evidence?
2. Are sets/reps/rest optimal for {ctx['focus']}?
3. Is exercise selection appropriate?
"""
        return query.strip()

    def _query_tavily(self, query: str) -> Dict:
        """Search Tavily with academic domain filtering."""
        if not self.tavily:
            return {"context": "", "citations": []}

        try:
            response = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_domains=ACADEMIC_DOMAINS
            )

            results = response.get("results", [])
            context = "\n".join([f"[Source: {r['url']}]\n{r['content']}" for r in results])
            citations = [r["url"] for r in results if r.get("url")]

            return {"context": context, "citations": citations}

        except Exception as e:
            print(f"⚠️  Tavily search error: {e}")
            return {"context": "", "citations": []}

    def _query_llm(self, query: str, goal: str, context: str = "") -> dict:
        if not self.llm.api_key:
            return {"error": "No LLM API key configured", "status_code": 500}

        if context:
            system_prompt = (
                f"You are a sports science researcher. Answer ONLY using the provided research context.\n\n"
                f"Retrieved Research:\n{context}\n\n"
                f"Respond in EXACTLY 3 structured points. Format each point as:\n\n"
                f"**Point 1 - [Heading]**: [3-4 concise sentences, no citation markers like [1] or [2] within text]\n"
                f"**Point 2 - [Heading]**: [3-4 concise sentences]\n"
                f"**Point 3 - [Heading]**: [3-4 concise sentences]\n\n"
                f"After the 3 points, list citations separately:\n[1] URL\n[2] URL\n\n"
                f"Rules: No markdown headers (#). No inline citation markers within body text. Max 4 sentences per point."
            )
            user_content = f"Analyze this {goal} prescription based on the provided research: {query}"
        else:
            system_prompt = (
                "You are a sports science researcher analyzing workout prescriptions.\n\n"
                "Respond in EXACTLY 3 structured points. Format each point as:\n\n"
                "**Point 1 - [Heading]**: [3-4 concise sentences, no citation markers like [1] or [2] within text]\n"
                "**Point 2 - [Heading]**: [3-4 concise sentences]\n"
                "**Point 3 - [Heading]**: [3-4 concise sentences]\n\n"
                "After the 3 points, list citations separately:\n[1] URL\n[2] URL\n\n"
                "Rules: No markdown headers (#). No inline citation markers within body text. Max 4 sentences per point."
            )
            user_content = f"Goal: {goal}\nPrescription: {query}"

        messages = [{"role": "user", "content": user_content}]

        return self.llm.generate(messages, system_prompt=system_prompt, temperature=0.1, max_tokens=500)

    def _parse_llm_response(self, response: dict, goal: str, tavily_citations: list) -> Dict:
        if "error" in response:
            return {"validated": False, "goal": goal, "evidence_summary": f"Error: {response['error']}", "citations": [], "confidence": "unknown", "validated_at": datetime.now().isoformat(), "source": "openrouter_error"}

        raw_response = response.get("content", "")
        api_citations = response.get("citations", [])
        text_urls = re.findall(r'https?://[^\s\)]+', raw_response)
        combined_urls = list(set(tavily_citations + api_citations + text_urls))

        citations = [u for u in combined_urls if not any(x in u.lower() for x in ['api.openrouter.ai', 'localhost', '127.0.0.1', 'example.com', 'streamlit.io'])]

        text = raw_response.lower()
        confidence = "medium"
        if any(kw in text for kw in ["strongly supported", "aligns with", "highly effective", "optimal"]):
            confidence = "high"
        if any(kw in text for kw in ["insufficient evidence", "no scientific evidence", "unsafe"]):
            confidence = "low"

        return {
            "validated": True,
            "goal": goal,
            "evidence_summary": raw_response,
            "citations": citations[:8] if citations else ['No direct citations available'],
            "confidence": confidence,
            "validated_at": datetime.now().isoformat(),
            "source": "openrouter_api"
        }
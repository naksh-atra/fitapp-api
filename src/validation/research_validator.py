# src/validation/research_validator.py
import os
import re
from typing import Dict

from tavily import TavilyClient
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


class ResearchValidator:
    """Validate exercise substitutions using Tavily + LLM (OpenRouter)"""

    SUBSTITUTION_CONTEXT = {
        "strength": "GREEN = similar 1RM loading potential and motor pattern. YELLOW = slight load reduction but same pattern. RED = fundamentally different pattern or significant load reduction.",
        "endurance": "GREEN = similar metabolic demand and rep tolerance at high reps. YELLOW = slightly lower endurance capacity. RED = exercise that limits reps or raises injury risk at high rep ranges.",
        "fatloss": "GREEN = similar caloric expenditure and heart rate elevation. YELLOW = lower metabolic output but acceptable. RED = low-intensity isolation that significantly reduces metabolic output.",
        "hypertrophy": "GREEN = similar muscle recruitment and volume capacity. YELLOW = 70-90% effective. RED = significant reduction in stimulus to target muscle."
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

        print(f"[ResearchValidator] Tavily: {'YES' if self.tavily else 'NO'}, LLM: {'YES' if self.llm.api_key else 'NO'}")

    def validate_exercise_swap(
        self,
        original: str,
        replacement: str,
        reason: str,
        goal: str = "hypertrophy"
    ) -> Dict:
        """
        Validate exercise substitution using Tavily (search) + LLM (synthesis).
        Returns GREEN/YELLOW/RED verdict with research backing.
        """
        try:
            search_context = ""
            citations = []

            if self.tavily:
                search_query = self.query_transformer.transform(
                    query=f"{original} vs {replacement}",
                    goal=goal,
                    original_exercise=original,
                    replacement_exercise=replacement
                )

                print(f"🔍 Tavily search: {search_query}")
                search_results = self._query_tavily(search_query)
                search_context = search_results.get("context", "")
                citations = search_results.get("citations", [])

            prompt = self._build_validation_prompt(original, replacement, reason, goal, search_context)
            system_instructions = "You are a research validator for exercise prescription. Evaluate exercise substitutions based on peer-reviewed evidence from 2020-2026. Return verdicts as GREEN (equivalent/valid), YELLOW (suboptimal but acceptable), or RED (not recommended)."

            messages = [{"role": "user", "content": prompt}]

            llm_response = self.llm.generate(messages, system_prompt=system_instructions, temperature=0.2, max_tokens=800)

            if "error" in llm_response:
                print(f"❌ LLM Error: {llm_response['error']}")
                return self._error_fallback(llm_response['error'])

            return self._parse_llm_response(llm_response, citations)

        except Exception as e:
            print(f"❌ Research Validator Crash: {e}")
            return self._error_fallback(str(e))

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

    def _error_fallback(self, error_str: str) -> Dict:
        return {
            "verdict": "red",
            "corrected_name": None,
            "reasoning": f"Validation system Error: {error_str}",
            "citations": [],
            "timestamp": None
        }

    def _build_validation_prompt(self, original, replacement, reason, goal, context: str = ""):
        goal_context = self.SUBSTITUTION_CONTEXT.get(goal, self.SUBSTITUTION_CONTEXT["hypertrophy"])

        base = f"""
Evaluate or suggest an exercise substitution for {goal}:

ORIGINAL: {original}
PROPOSED REPLACEMENT: {replacement}
REASON: {reason}

INSTRUCTION:
1. Evaluate biomechanical equivalence and effectiveness.
2. Analyze muscle activation (cite research 2020-2026).
3. Recommend a CANONICAL NAME if the input is vague.

Format response:
CANONICAL NAME: [Name]
VERDICT: [GREEN/YELLOW/RED]
PERCENTAGE: [XX]%

Analysis: [Details...]

Criteria for {goal}: {goal_context}
"""

        if context:
            base = f"Provided Research Context:\n{context}\n\n{base}"

        return base

    def _parse_llm_response(self, response: Dict, tavily_citations: list) -> Dict:
        content = response.get("content", "")

        if not content:
            return self._error_fallback("Empty LLM response")

        citations = list(set(tavily_citations + response.get("citations", [])))

        canonical_match = re.search(r"CANONICAL NAME:\s*(.*)", content, re.IGNORECASE)
        corrected_name = canonical_match.group(1).strip() if canonical_match else None

        content_upper = content.upper()
        if "GREEN" in content_upper:
            verdict = "green"
        elif "YELLOW" in content_upper:
            verdict = "yellow"
        elif "RED" in content_upper:
            verdict = "red"
        else:
            verdict = "yellow"

        return {
            "verdict": verdict,
            "corrected_name": corrected_name,
            "reasoning": content,
            "citations": citations,
            "timestamp": response.get("created")
        }
import os
import re
from typing import Dict, Optional

from .llm_client import LLMClient


GOAL_KEYWORDS = {
    "hypertrophy": ["muscle protein synthesis", "muscle growth", "volume", "mechanical tension"],
    "strength": ["1RM", "progressive overload", "maximal strength", "neural adaptations"],
    "fatloss": ["metabolic rate", "caloric expenditure", "EPOC", "body composition"],
    "endurance": ["muscular endurance", "aerobic capacity", "oxidative capacity", "type I fibers"]
}

YEAR_PREFERENCE = "2023-2025"
YEAR_RANGE = "2020-2026"
MAX_QUERY_LENGTH = 400


EXERCISE_TERM_MAP = {
    "squat": "barbell back squat quadriceps",
    "bench press": "barbell bench press pectoral muscle",
    "deadlift": "barbell deadlift posterior chain",
    "overhead press": "overhead press shoulder deltoids",
    "pull up": "pull-up latissimus dorsi",
    "chin up": "chin-up bicep brachii",
    "row": "barbell row latissimus dorsi",
    "curl": "bicep curl brachii",
    "extension": "tricep extension",
    "press": "overhead press",
    "leg press": "leg press quadriceps",
    "lunges": "walking lunges quadriceps",
    "plank": "plank core stabilization",
    "push up": "push-up pectoral muscle",
    "pushup": "push-up pectoral muscle",
}


class QueryTransformer:
    """Transforms raw user queries into search-optimized queries for Tavily."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self._term_map = EXERCISE_TERM_MAP.copy()

    def transform(
        self,
        query: str,
        goal: str = "hypertrophy",
        original_exercise: Optional[str] = None,
        replacement_exercise: Optional[str] = None
    ) -> str:
        """
        Transform user query into a search-optimized query.

        Args:
            query: Raw user input (e.g., "leg workout at home")
            goal: One of hypertrophy, strength, fatloss, endurance
            original_exercise: Original exercise in swap (e.g., "bench press")
            replacement_exercise: Replacement exercise (e.g., "push-ups")

        Returns:
            Transformed query optimized for Tavily search (max 400 chars)
        """
        goal = goal.lower()
        if goal not in GOAL_KEYWORDS:
            goal = "hypertrophy"

        transformed = query

        transformed = self._expand_terms(transformed)

        if original_exercise and replacement_exercise:
            transformed = self._build_dual_comparison(
                original_exercise,
                replacement_exercise,
                goal
            )
        else:
            transformed = self._add_goal_context(transformed, goal)

        transformed = self._add_year_constraint(transformed)

        transformed = self._truncate_to_max(transformed)

        return transformed

    def _expand_terms(self, text: str) -> str:
        """Expand common exercise names to scientific/technical terms."""
        text_lower = text.lower()

        for common, expanded in self._term_map.items():
            if common in text_lower:
                text = text.replace(common, f"{common} {expanded}", 1)

        return text

    def _build_dual_comparison(
        self,
        original: str,
        replacement: str,
        goal: str
    ) -> str:
        """
        Build a single query comparing two exercises.

        Note: Alternative approach (commented) could use parallel queries:
        - Query 1: Original exercise alone
        - Query 2: Replacement exercise alone
        - Query 3: Direct comparison

        Current: Single query with both + "vs" for direct comparison research
        """
        orig_expanded = self._expand_terms(original).strip()
        repl_expanded = self._expand_terms(replacement).strip()

        goal_keywords = GOAL_KEYWORDS.get(goal, GOAL_KEYWORDS["hypertrophy"])
        goal_hint = ", ".join(goal_keywords[:2])

        query = f"{orig_expanded} vs {repl_expanded} {goal_hint} research"

        return query

    def _add_goal_context(self, query: str, goal: str) -> str:
        """Add goal-specific keywords to the query."""
        goal_keywords = GOAL_KEYWORDS.get(goal, GOAL_KEYWORDS["hypertrophy"])

        if goal_keywords[0] not in query.lower():
            query = f"{query} {goal_keywords[0]}"

        return query

    def _add_year_constraint(self, query: str) -> str:
        """Add year range constraint for recent research."""
        if YEAR_PREFERENCE not in query and YEAR_RANGE not in query:
            query = f"{query} {YEAR_PREFERENCE}"

        return query

    def _truncate_to_max(self, query: str) -> str:
        """Truncate query to max 400 characters (Tavily free tier limit)."""
        if len(query) > MAX_QUERY_LENGTH:
            query = query[:MAX_QUERY_LENGTH - 3].rsplit(" ", 1)[0] + "..."

        return query

    def transform_with_llm(
        self,
        query: str,
        goal: str = "hypertrophy",
        original_exercise: Optional[str] = None,
        replacement_exercise: Optional[str] = None
    ) -> str:
        """
        Transform query using LLM for more sophisticated term expansion.

        This uses the LLM to expand scientific terminology beyond the basic
        term mapping, providing better search targeting.

        Args:
            query: Raw user input
            goal: fitness goal
            original_exercise: Original exercise in swap
            replacement_exercise: Replacement exercise

        Returns:
            LLM-optimized query
        """
        system_prompt = """You are a search query optimizer for sports science research.
Transform user exercise queries into search-optimized queries for academic research databases.

Rules:
1. Convert casual exercise names to scientific/technical terms
2. Add relevant research keywords based on goal (hypertrophy, strength, fatloss, endurance)
3. Add year range "2023-2025" for recent research
4. Keep query under 300 characters
5. Use exercise-specific terminology (e.g., "pectoral muscle" not "chest")
6. For exercise comparisons, include "vs" and both exercises

Example transformations:
- "leg workout" -> "lower body resistance training quadriceps hypertrophy 2023-2025"
- "bench press vs pushups" -> "barbell bench press vs push-ups pectoral muscle activation research 2023-2025"
- "bigger arms" -> "bicep brachii hypertrophic training muscle growth 2023-2025"

Output ONLY the transformed query, nothing else."""

        user_prompt = f"Transform this query: {query}"
        if original_exercise and replacement_exercise:
            user_prompt = f"Transform for exercise swap: {original_exercise} -> {replacement_exercise}"

        result = self.llm.generate(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=150
        )

        if "error" in result:
            return self.transform(query, goal, original_exercise, replacement_exercise)

        transformed = result["content"].strip()

        transformed = self._truncate_to_max(transformed)

        return transformed
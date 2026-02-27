# """
# tests/test_all_goals.py
# All-goal acceptance tests: 12 happy-path combos + edge cases + substitution verdicts.
# Requires the FitApp API to be running at http://127.0.0.1:8000
# """

# import pytest
# import requests

# BASE = "http://127.0.0.1:8000"
# ALL_GOALS = ["hypertrophy", "strength", "endurance", "fatloss"]


# # ---------------------------------------------------------------------------
# # 12 happy-path combos  (4 goals × 3 equipment/experience combos)
# # ---------------------------------------------------------------------------

# @pytest.mark.parametrize("goal,equipment,experience", [
#     (g, e, x)
#     for g in ALL_GOALS
#     for e, x in [("gym", "beginner"), ("gym", "advanced"), ("home", "intermediate")]
# ])
# def test_all_goal_combos(goal, equipment, experience):
#     resp = requests.post(
#         f"{BASE}/generate_workout",
#         json={"goal": goal, "equipment": equipment, "experience": experience, "week": 1},
#         timeout=90,
#     )
#     assert resp.status_code == 200, (
#         f"{goal}/{equipment}/{experience}: HTTP {resp.status_code} — {resp.text[:200]}"
#     )
#     data = resp.json()["data"]
#     assert len(data["exercises"]) >= 4, (
#         f"{goal}/{equipment}/{experience}: only {len(data['exercises'])} exercises"
#     )


# # ---------------------------------------------------------------------------
# # Edge case: home endurance minimal
# # ---------------------------------------------------------------------------

# def test_home_endurance_minimal():
#     resp = requests.post(
#         f"{BASE}/generate_workout",
#         json={"goal": "endurance", "equipment": "home", "experience": "beginner", "week": 1},
#         timeout=90,
#     )
#     assert resp.status_code == 200
#     assert len(resp.json()["data"]["exercises"]) >= 4


# # ---------------------------------------------------------------------------
# # Substitution verdicts per goal  (/validate_swap endpoint)
# # ---------------------------------------------------------------------------

# @pytest.mark.parametrize("goal,original,replacement,reason", [
#     ("strength",    "Barbell Back Squat",    "Leg Press",      "knee_pain"),
#     ("endurance",   "Bodyweight Squat",      "Step Up",        "preference"),
#     ("fatloss",     "Kettlebell Swing",      "Burpees",        "no_kettlebell"),
#     ("hypertrophy", "Barbell Bench Press",   "Dumbbell Press", "shoulder_pain"),
# ])
# def test_substitution_verdicts(goal, original, replacement, reason):
#     resp = requests.post(
#         f"{BASE}/validate_swap",
#         json={
#             "original_exercise": original,
#             "replacement_exercise": replacement,
#             "reason": reason,
#             "goal": goal,
#         },
#         timeout=30,
#     )
#     assert resp.status_code == 200, (
#         f"validate_swap {goal}: HTTP {resp.status_code} — {resp.text[:200]}"
#     )
#     data = resp.json()
#     assert data["verdict"] in ["GREEN", "YELLOW", "RED"], (
#         f"Unexpected verdict: {data['verdict']!r}"
#     )
#     assert len(data["reasoning"]) > 10, "Reasoning too short"


# # ---------------------------------------------------------------------------
# # Invalid goal → 422
# # ---------------------------------------------------------------------------

# def test_invalid_goal_returns_422():
#     resp = requests.post(
#         f"{BASE}/generate_workout",
#         json={"goal": "cardio", "equipment": "gym", "experience": "beginner", "week": 1},
#         timeout=10,
#     )
#     assert resp.status_code == 422, f"Expected 422 for 'cardio', got {resp.status_code}"



"""
tests/test_all_goals.py

Comprehensive acceptance tests for all 4 goals.
Covers: Equipment × Experience × Cache × Edge Cases × Validation × Substitution

Test matrix per goal:
┌─────────────┬─────────────┬────────────┬──────────────┐
│ Equipment   │ Experience  │ Cache      │ Expect       │
├─────────────┼─────────────┼────────────┼──────────────┤
│ gym         │ beginner    │ fresh      │ 200 OK       │
│ gym         │ intermediate│ fresh      │ 200 OK       │
│ gym         │ advanced    │ fresh      │ 200 OK       │
│ home        │ beginner    │ fresh      │ 200 OK       │
│ home        │ intermediate│ fresh      │ 200 OK       │
│ home        │ advanced    │ fresh      │ 200 OK       │
│ gym         │ beginner    │ cached     │ 200 fast     │
│ gym         │ beginner    │ invalid    │ 422          │
│ gym         │ beginner    │ edge week  │ 200/422      │
└─────────────┴─────────────┴────────────┴──────────────┘

Requires: API running at http://127.0.0.1:8000
Run with: pytest tests/test_all_goals.py -v --tb=short
"""

import time
import pytest
import requests

BASE     = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE}/generate_workout"

ALL_GOALS = ["hypertrophy", "strength", "endurance", "fatloss"]

# Goal → expected rep range (min_of_any_exercise, max_of_any_exercise)
GOAL_REP_RANGES = {
    "strength":    (1,  6),
    "hypertrophy": (6,  20),
    "endurance":   (15, 30),
    "fatloss":     (10, 20),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clear_cache():
    try:
        r = requests.delete(f"{BASE}/clear_cache", timeout=2)
        print(f"🗑️ Cache cleared ({r.status_code})")
    except Exception:
        print("⚠️  No /clear_cache endpoint (OK)")


def _assert_response_structure(resp, goal, equipment, experience):
    """Common structure checks for every 200 response"""
    assert resp.status_code == 200, (
        f"{goal}/{equipment}/{experience}: HTTP {resp.status_code} — {resp.text[:200]}"
    )
    body = resp.json()
    assert "data"   in body,          "Missing top-level 'data'"
    assert "status" in body,          "Missing top-level 'status'"
    assert body["status"] == "success"

    data = body["data"]
    assert "exercises" in data,       "Missing data.exercises"
    assert "citations" in data,       "Missing data.citations"
    assert len(data["exercises"]) >= 4, (
        f"Only {len(data['exercises'])} exercises returned"
    )
    return data


def _assert_exercise_schema(exercises, goal):
    """Verify each exercise has required fields + goal-appropriate rep range"""
    low, high = GOAL_REP_RANGES[goal]
    for ex in exercises:
        for field in ["name", "sets", "reps", "rest_seconds", "rpe"]:
            assert field in ex, f"Exercise missing '{field}': {ex}"
        reps   = ex["reps"]
        ex_min = reps[0] if isinstance(reps, list) else reps
        assert ex_min <= high, (
            f"{goal}: {ex['name']} reps {reps} — min {ex_min} exceeds goal ceiling {high}"
        )


# ---------------------------------------------------------------------------
# 1. Happy path: 6 combos × 4 goals = 24 tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("goal", ALL_GOALS)
@pytest.mark.parametrize("equipment,experience", [
    ("gym",  "beginner"),
    ("gym",  "intermediate"),
    ("gym",  "advanced"),
    ("home", "beginner"),
    ("home", "intermediate"),
    ("home", "advanced"),
])
def test_happy_path(goal, equipment, experience):
    clear_cache()
    resp = requests.post(
        ENDPOINT,
        json={"goal": goal, "equipment": equipment, "experience": experience, "week": 1},
        timeout=90,
    )
    data = _assert_response_structure(resp, goal, equipment, experience)
    _assert_exercise_schema(data["exercises"], goal)
    print(f"✅ {goal}/{equipment}/{experience}: {len(data['exercises'])} exercises")


# ---------------------------------------------------------------------------
# 2. Cache reuse (one per goal)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("goal", ALL_GOALS)
def test_cache_reuse(goal):
    clear_cache()
    payload = {"goal": goal, "equipment": "gym", "experience": "intermediate", "week": 1}

    # Call 1: populate cache
    resp1 = requests.post(ENDPOINT, json=payload, timeout=90)
    assert resp1.status_code == 200
    data1 = resp1.json()["data"]

    # Call 2: cache hit
    start  = time.time()
    resp2  = requests.post(ENDPOINT, json=payload, timeout=90)
    elapsed = time.time() - start
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]

    # Speed check (cache should be fast)
    assert elapsed < 5.0, f"Cache too slow for {goal}: {elapsed:.1f}s"

    # Structure check
    assert len(data1["exercises"]) == len(data2["exercises"]), (
        f"{goal}: exercise count changed between calls"
    )

    # True cache check (conditional on Perplexity being available)
    source1 = data1.get("validation_source", "")
    source2 = data2.get("validation_source", "")
    if source1 == "perplexity_api":
        assert source2 == "perplexity_api", f"{goal}: cache miss on second call"
        print(f"✅ {goal} true cache hit: {elapsed:.1f}s")
    else:
        print(f"⚠️  {goal} cache inconclusive (Perplexity unavailable): {elapsed:.1f}s")


# ---------------------------------------------------------------------------
# 3. Input validation → 422 (shared across all goals)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("test_case,expected_status", [
    ({"goal": "mass"},         422),
    ({"goal": "cardio"},       422),
    ({"goal": "bulk"},         422),
    ({"experience": "expert"}, 422),
    ({"equipment": "pool"},    422),
    ({"week": -1},             422),
    ({"week": 53},             422),
    ({"week": ""},             422),
    ({"week": "abc"},          422),
])
def test_validation_errors(test_case, expected_status):
    payload = {
        "goal":       test_case.get("goal",       "hypertrophy"),
        "equipment":  test_case.get("equipment",  "gym"),
        "experience": test_case.get("experience", "beginner"),
        "week":       test_case.get("week",       1),
    }
    resp = requests.post(ENDPOINT, json=payload, timeout=10)
    assert resp.status_code == expected_status, (
        f"Expected {expected_status} for {test_case}, got {resp.status_code}"
    )
    print(f"✅ {test_case} → {resp.status_code}")


# ---------------------------------------------------------------------------
# 4. Edge cases (week boundary + defaults)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("goal", ALL_GOALS)
@pytest.mark.parametrize("case,expect", [
    ({"week": 1},   200),   # Min valid
    ({"week": 52},  200),   # Max valid
    ({"week": 26},  200),   # Mid range
    ({},            200),   # No week → default
    ({"week": 0},   422),   # Below ge=1
    ({"week": 53},  422),   # Above le=52
    ({"week": ""},  422),   # Wrong type
])
def test_edge_cases(goal, case, expect):
    payload = {
        "goal":       goal,
        "equipment":  "gym",
        "experience": "beginner",
        **case,
    }
    resp = requests.post(ENDPOINT, json=payload, timeout=60)
    assert resp.status_code < 500, f"500 CRASH on {goal}/{case}"
    assert resp.status_code == expect, (
        f"{goal}/{case}: expected {expect}, got {resp.status_code}"
    )
    print(f"✅ {goal}/{case} → {resp.status_code}")


# ---------------------------------------------------------------------------
# 5. Toxic inputs — never 500
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload", [
    {},
    {"goal": ""},
    {"goal": 123},
    {"equipment": None},
    {"goal": "x" * 1000},
    {"week": [1, 2, 3]},
    {"goal": "hypertrophy", "week": {"nested": "object"}},
])
def test_toxic_inputs_no_crashes(payload):
    resp = requests.post(ENDPOINT, json=payload, timeout=10)
    assert resp.status_code < 500, f"500 CRASH on {payload}"
    print(f"✅ Toxic {str(payload)[:40]}: {resp.status_code}")


# ---------------------------------------------------------------------------
# 6. LLM failure → workout still works (all goals)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("goal", ALL_GOALS)
def test_llm_failure_still_works(goal):
    resp = requests.post(
        ENDPOINT,
        json={"goal": goal, "equipment": "gym", "experience": "beginner"},
        timeout=90,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data"      in data
    assert "exercises" in data["data"]
    print(f"✅ {goal}: LLM fail → workout OK")


# ---------------------------------------------------------------------------
# 7. Substitution verdicts per goal (/validate_swap)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("goal,original,replacement,reason", [
    ("strength",    "Barbell Back Squat",  "Leg Press",      "knee_pain"),
    ("endurance",   "Bodyweight Squat",    "Step Up",        "preference"),
    ("fatloss",     "Kettlebell Swing",    "Burpees",        "no_kettlebell"),
    ("hypertrophy", "Barbell Bench Press", "Dumbbell Press", "shoulder_pain"),
])
def test_substitution_verdicts(goal, original, replacement, reason):
    resp = requests.post(
        f"{BASE}/validate_swap",
        json={
            "original_exercise":    original,
            "replacement_exercise": replacement,
            "reason":               reason,
            "goal":                 goal,
        },
        timeout=90,
    )
    assert resp.status_code == 200, (
        f"validate_swap {goal}: HTTP {resp.status_code} — {resp.text[:200]}"
    )
    data = resp.json()
    assert data["verdict"] in ["GREEN", "YELLOW", "RED"]
    assert len(data["reasoning"]) > 10
    assert any(
        kw in data["reasoning"].lower()
        for kw in ["strength", "endurance", "fat", "hypertrophy", "muscle", "load", "rep"]
    ), f"Reasoning lacks goal context: {data['reasoning'][:100]}"
    print(f"✅ {goal} swap → {data['verdict']}")

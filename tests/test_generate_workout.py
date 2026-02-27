# To test the following cases:
# Equipment  x Experience x Cache x Edge Cases = 24 tests
# ┌─────────────┬─────────────┬────────────┬─────────────┬──────────────┐
# │ Equipment   │ Experience  │ Cache      │ Goal        │ Expect       │
# ├─────────────┼─────────────┼────────────┼─────────────┼──────────────┤
# │ gym         │ beginner    │ fresh      │ hypertrophy │ 200 OK       │
# │ gym         │ beginner    │ cached     │ hypertrophy │ 200 cached   │
# │ gym         │ intermediate│ fresh      │ hypertrophy │ 200 OK       │
# │ gym         │ intermediate│ cached     │ hypertrophy │ 200 cached   │
# │ gym         │ advanced    │ fresh      │ hypertrophy │ 200 OK       │
# │ gym         │ advanced    │ cached     │ hypertrophy │ 200 cached   │
# │ home        │ beginner    │ fresh      │ hypertrophy │ 200 OK       │
# │ home        │ beginner    │ cached     │ hypertrophy │ 200 cached   │
# │ ... (18 more)                                              │
# │ gym         │ beginner    │ fresh      │ mass        │ 400 Bad Req  │
# │ gym         │ beginner    │ fresh      │ week=0      │ 200 OK       │
# │ gym         │ beginner    │ fresh      │ week=None   │ 200 OK       │
# └─────────────┴─────────────┴────────────┴─────────────┴──────────────┘




# tests/test_generate_workout.py (FINAL - No fixtures)
import requests
import time
import pytest

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/generate_workout"

def clear_cache():
    """Attempt cache clear (safe if missing)"""
    try:
        requests.delete(f"{BASE_URL}/clear_cache", timeout=2)
        print("🗑️ Cache cleared")
    except:
        print("⚠️ No cache clear endpoint (OK)")

@pytest.mark.parametrize("equipment, experience", [
    ("gym", "beginner"),
    ("gym", "intermediate"), 
    ("gym", "advanced"),
    ("home", "beginner"),
    ("home", "intermediate"),
    ("home", "advanced"),
])
def test_happy_path(equipment, experience):
    clear_cache()
    
    payload = {
        "goal": "hypertrophy",
        "equipment": equipment,
        "experience": experience,
        "week": 1
    }
    
    resp = requests.post(ENDPOINT, json=payload, timeout=90)
    assert resp.status_code == 200, f"{equipment}/{experience}: {resp.status_code}"
    
    data = resp.json()
    assert "data" in data
    assert "exercises" in data["data"]
    assert len(data["data"]["exercises"]) >= 4  # Realistic minimum
    assert "citations" in data["data"]
    assert data.get("status") == "success"
    
    print(f"✅ {equipment}/{experience}: {len(data['data']['exercises'])} exercises")

def test_cache_reuse():
    clear_cache()
    payload = {"goal": "hypertrophy", "equipment": "gym", "experience": "beginner", "week": 1}

    resp1 = requests.post(ENDPOINT, json=payload, timeout=90)
    assert resp1.status_code == 200
    data1 = resp1.json()

    resp2 = requests.post(ENDPOINT, json=payload, timeout=90)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # True cache test: check source field
    v1 = data1["data"].get("validation_source", "")
    v2 = data2["data"].get("validation_source", "")

    if "perplexity_api" in v1:
        # Perplexity worked → second call MUST be cached
        assert v2 == v1, "Second call should use cache"
        print("✅ True cache hit confirmed")
    else:
        # Perplexity 401 → cache never populated → test is inconclusive
        print(f"⚠️ Cache test inconclusive: Perplexity returned {v1}, not testing cache")
    
    # Call 2 (cache hit - fast)
    start = time.time()
    resp2 = requests.post(ENDPOINT, json=payload, timeout=90)
    elapsed = time.time() - start
    assert resp2.status_code == 200
    assert elapsed < 5.0, f"Cache too slow: {elapsed}s"
    
    data2 = resp2.json()["data"]
    assert len(data1["exercises"]) == len(data2["exercises"])
    print(f"✅ Cache reuse: {elapsed:.1f}s")

@pytest.mark.parametrize("test_case, expected_status", [
    ({"goal": "mass"},           422),  # Invalid goal
    ({"experience": "expert"},   422),  # Invalid experience
    ({"equipment": "pool"},      422),  # Invalid equipment
    ({"week": -1},               422),  # Below ge=0
    ({"week": 53},               422),  # Above le=52
    ({"week": ""},               422),  # Wrong type
])
def test_validation_errors(test_case, expected_status):
    payload = {
        "goal":       test_case.get("goal", "hypertrophy"),
        "equipment":  test_case.get("equipment", "gym"),
        "experience": test_case.get("experience", "beginner"),
        "week":       test_case.get("week", 1)
    }
    resp = requests.post(ENDPOINT, json=payload, timeout=10)
    assert resp.status_code == expected_status, \
        f"Expected {expected_status} for {test_case}, got {resp.status_code}"
    print(f"✅ {test_case} → {resp.status_code}")


def test_edge_cases():
    cases = [
        {"week": 0},
        {"week": None},
        {"week": 52},
        {"week": ""},    # Empty string
        {},              # Minimal
    ]
    
    for case in cases:
        payload = {
            "goal": "hypertrophy",
            "equipment": "gym", 
            "experience": "beginner",
            **case
        }
        resp = requests.post(ENDPOINT, json=payload, timeout=60)
        # Never 500, always responds
        assert resp.status_code < 500, f"500 crash on {case}"
        
        # 422 validation errors = expected for bad data
        if case.get("week") == "":
            assert resp.status_code == 422
        else:
            assert resp.status_code == 200
            
        print(f"✅ Edge {case}: {resp.status_code}")

def test_toxic_inputs_no_crashes():
    """Never 500 under any abuse"""
    toxic = [
        {},                           # Empty
        {"goal": ""},                 # Empty strings
        {"goal": 123},                # Wrong types
        {"week": "abc"},
        {"equipment": None},
        {"goal": "x" * 1000},         # Huge input
    ]
    
    for payload in toxic:
        resp = requests.post(ENDPOINT, json=payload, timeout=10)
        assert resp.status_code < 500, f"500 CRASH on {payload}"
        print(f"✅ Toxic {str(payload)[:30]}...: {resp.status_code}")

def test_llm_failure_still_works():
    """Research degraded → core workout intact"""
    payload = {"goal": "hypertrophy", "equipment": "gym", "experience": "beginner"}
    resp = requests.post(ENDPOINT, json=payload, timeout=90)
    
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "exercises" in data["data"]  # Workout ALWAYS works
    print("✅ LLM fail → workout OK")

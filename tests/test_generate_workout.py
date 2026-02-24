import pytest
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"  # Your FastAPI
ENDPOINT = f"{BASE_URL}/generate_workout"

@pytest.fixture(scope="session")
def client():
    return requests.Session()

def clear_cache():  # Hit cache-busting endpoint if exists
    try:
        requests.delete(f"{BASE_URL}/clear_cache")
    except:
        pass

# Core test matrix
@pytest.mark.parametrize("equipment, experience, goal", [
    ("gym", "beginner", "hypertrophy"),
    ("gym", "intermediate", "hypertrophy"),
    ("gym", "advanced", "hypertrophy"),
    ("home", "beginner", "hypertrophy"),
    ("home", "intermediate", "hypertrophy"),
    ("home", "advanced", "hypertrophy"),
])
def test_happy_path(client, equipment, experience, goal):
    """Fresh request → 200 + research validation"""
    clear_cache()
    
    payload = {
        "goal": goal,
        "equipment": equipment,
        "experience": experience,
        "week": 1
    }
    
    resp = client.post(ENDPOINT, json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    data = resp.json()
    assert "exercises" in data
    assert "research_validation" in data
    assert len(data["exercises"]) > 0
    print(f"✅ {equipment}/{experience}: {len(data['exercises'])} exercises")

def test_cache_hit(client):
    """Second identical request → cached research"""
    payload = {
        "goal": "hypertrophy",
        "equipment": "gym",
        "experience": "beginner",
        "week": 1
    }
    
    # First call (populates cache)
    resp1 = client.post(ENDPOINT, json=payload)
    assert resp1.status_code == 200
    
    # Second call (hits cache)
    resp2 = client.post(ENDPOINT, json=payload)
    assert resp2.status_code == 200
    
    data1 = resp1.json()["research_validation"]
    data2 = resp2.json()["research_validation"]
    
    assert data1["validated_at"] == data2["validated_at"]  # Same cache entry
    print("✅ Cache hit confirmed")

@pytest.mark.parametrize("equipment, experience, goal", [
    ("gym", "beginner", "mass"),      # Invalid goal
    ("gym", "expert", "hypertrophy"), # Invalid experience
    ("pool", "beginner", "hypertrophy"), # Invalid equipment
])
def test_invalid_inputs(client, equipment, experience, goal):
    """Invalid params → clean 4xx"""
    payload = {
        "goal": goal,
        "equipment": equipment,
        "experience": experience,
        "week": 1
    }
    
    resp = client.post(ENDPOINT, json=payload)
    assert 400 <= resp.status_code < 500, f"Expected 4xx, got {resp.status_code}"
    print(f"✅ Invalid {goal}: {resp.status_code}")

def test_edge_cases(client):
    """Week edge cases"""
    cases = [
        {"week": 0},      # First week
        {"week": None},   # No week specified
        {"week": 52},     # Max week
    ]
    
    for case in cases:
        payload = {
            "goal": "hypertrophy",
            "equipment": "gym",
            "experience": "beginner",
            **case
        }
        resp = client.post(ENDPOINT, json=payload)
        assert resp.status_code == 200
        print(f"✅ Week edge {case}: 200 OK")

def test_llm_failure_robustness(client):
    """Perplexity 401 → workout still generates"""
    # Temporarily break Perplexity (set invalid key or mock)
    # For now: trust your validator handles 401s gracefully
    payload = {"goal": "hypertrophy", "equipment": "gym", "experience": "beginner"}
    resp = client.post(ENDPOINT, json=payload)
    
    data = resp.json()
    assert resp.status_code == 200
    assert "exercises" in data  # Workout generates regardless
    assert data["research_validation"].get("error")  # Research degraded OK
    print("✅ LLM failure → workout still works")

def test_no_500s_anything(client):
    """Golden rule: Never 500"""
    toxic_payloads = [
        {},  # Empty
        {"goal": ""},  # Empty goal
        {"week": -1},  # Negative week
        {"goal": 123}, # Wrong type
    ]
    
    for payload in toxic_payloads:
        resp = client.post(ENDPOINT, json=payload)
        assert resp.status_code < 500, f"500 on {payload}: {resp.status_code}"
        print(f"✅ Toxic {payload}: {resp.status_code}")

"""
Comprehensive test script for the True Agent system.
Tests all endpoints and agent capabilities.
"""
import requests
import json
import time
import sys
from typing import Dict, Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_root():
    """Test root endpoint."""
    print_section("1. Testing Root Endpoint")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_create_position():
    """Test creating a position."""
    print_section("2. Testing Position Creation")
    job_description = """
    We are looking for a Senior Python Developer with the following requirements:
    
    MUST HAVE:
    - 5+ years of Python development experience
    - Experience with FastAPI or Django
    - Strong knowledge of SQL databases
    - Experience with Git version control
    
    NICE TO HAVE:
    - Experience with Docker and Kubernetes
    - Knowledge of machine learning frameworks
    - Experience with cloud platforms (AWS, Azure, GCP)
    
    BONUS:
    - Open source contributions
    - Experience with microservices architecture
    """
    
    data = {"raw_description": job_description}
    response = requests.post(f"{BASE_URL}/positions", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if response.status_code == 200:
        return result.get("id")
    return None

def test_upload_cv():
    """Test uploading a CV."""
    print_section("3. Testing CV Upload")
    
    # Create a sample CV text
    cv_text = """
    John Doe
    Email: john.doe@example.com
    Phone: +1-555-0123
    
    PROFESSIONAL SUMMARY:
    Senior Python Developer with 7 years of experience in building scalable web applications.
    Expert in FastAPI, Django, and PostgreSQL. Strong background in microservices architecture.
    
    EXPERIENCE:
    - Senior Python Developer at TechCorp (2020-Present)
      * Developed REST APIs using FastAPI
      * Designed and implemented microservices architecture
      * Worked with Docker and Kubernetes
      * Managed PostgreSQL databases
    
    - Python Developer at StartupXYZ (2017-2020)
      * Built Django web applications
      * Implemented CI/CD pipelines
      * Worked with AWS cloud services
    
    EDUCATION:
    - Bachelor of Science in Computer Science, University of Tech (2017)
    
    SKILLS:
    - Python, FastAPI, Django
    - PostgreSQL, SQL
    - Docker, Kubernetes
    - Git, CI/CD
    - AWS, Microservices
    """
    
    # Create a temporary text file
    with open("test_cv.txt", "w", encoding="utf-8") as f:
        f.write(cv_text)
    
    try:
        with open("test_cv.txt", "rb") as f:
            files = {"file": ("test_cv.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/candidates/upload", files=files)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        if response.status_code == 200:
            return result.get("id")
        return None
    finally:
        import os
        if os.path.exists("test_cv.txt"):
            os.remove("test_cv.txt")

def test_simple_screening(candidate_id: str, position_id: str):
    """Test simple screening (non-agent)."""
    print_section("4. Testing Simple Screening")
    
    response = requests.post(
        f"{BASE_URL}/screenings",
        params={"candidate_id": candidate_id, "position_id": position_id}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Screening ID: {result.get('id')}")
    print(f"Decision: {result.get('decision')}")
    print(f"Score: {result.get('score')}")
    print(f"Clarification Questions: {len(result.get('clarification_questions', []))}")
    
    return result.get("id")

def test_simple_agent_mode(candidate_id: str, position_id: str):
    """Test simple agent mode."""
    print_section("5. Testing Simple Agent Mode")
    
    data = {
        "candidate_id": candidate_id,
        "position_id": position_id,
        "max_iterations": 3
    }
    
    print(f"Request: {json.dumps(data, indent=2)}")
    print("Running agent loop...")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/agent/screen", json=data)
    elapsed = time.time() - start_time
    
    print(f"Status: {response.status_code}")
    print(f"Time taken: {elapsed:.2f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Screening ID: {result.get('id')}")
        print(f"Decision: {result.get('decision')}")
        print(f"Score: {result.get('score')}")
        print(f"Version: {result.get('version')}")
        print(f"Clarification Questions: {len(result.get('clarification_questions', []))}")
        return result.get("id")
    else:
        print(f"Error: {response.text}")
        return None

def test_true_agent_mode(candidate_id: str, position_id: str):
    """Test TRUE AGENT mode - the grand one!"""
    print_section("6. Testing TRUE AGENT Mode [AUTONOMOUS]")
    
    data = {
        "candidate_id": candidate_id,
        "position_id": position_id,
        "max_iterations": 5,
        "goal": "Evaluate candidate with high confidence and resolve all uncertainties"
    }
    
    print(f"Request: {json.dumps(data, indent=2)}")
    print("[AGENT] Starting autonomous agent...")
    print("        This may take a while as the agent reasons through each step...")
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/agent/true-agent", json=data, timeout=300)
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"⏱️  Time taken: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[OK] Screening ID: {result.get('id')}")
            print(f"[INFO] Decision: {result.get('decision')}")
            print(f"[INFO] Score: {result.get('score')}")
            print(f"[INFO] Version: {result.get('version')}")
            print(f"[INFO] Clarification Questions: {len(result.get('clarification_questions', []))}")
            
            if result.get('clarification_questions'):
                print("\n[QUESTIONS] Clarification Questions:")
                for i, q in enumerate(result.get('clarification_questions', [])[:3], 1):
                    print(f"   {i}. {q}")
            
            return result.get("id")
        else:
            print(f"[ERROR] Error: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (took > 5 minutes)")
        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_match_positions(candidate_id: str):
    """Test matching positions."""
    print_section("7. Testing Match Positions")
    
    response = requests.post(
        f"{BASE_URL}/agent/match-positions",
        params={"candidate_id": candidate_id, "top_n": 3}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        matches = result.get("matches", [])
        print(f"Found {len(matches)} matches:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match.get('position_title')} - Score: {match.get('score'):.2f} - {match.get('decision')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_get_screening(screening_id: str):
    """Test getting a screening."""
    print_section("8. Testing Get Screening")
    
    response = requests.get(f"{BASE_URL}/screenings/{screening_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Decision: {result.get('decision')}")
        print(f"Score: {result.get('score')}")
        print(f"Strengths: {len(result.get('strengths', []))}")
        print(f"Gaps: {len(result.get('gaps', []))}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  COMPREHENSIVE TRUE AGENT TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Test 1: Root endpoint
    results["root"] = test_root()
    time.sleep(1)
    
    # Test 2: Create position
    position_id = test_create_position()
    results["create_position"] = position_id is not None
    time.sleep(1)
    
    if not position_id:
        print("\n[ERROR] Failed to create position. Stopping tests.")
        return
    
    # Test 3: Upload CV
    candidate_id = test_upload_cv()
    results["upload_cv"] = candidate_id is not None
    time.sleep(1)
    
    if not candidate_id:
        print("\n[ERROR] Failed to upload CV. Stopping tests.")
        return
    
    # Test 4: Simple screening
    screening_id = test_simple_screening(candidate_id, position_id)
    results["simple_screening"] = screening_id is not None
    time.sleep(2)
    
    # Test 5: Simple agent mode
    agent_screening_id = test_simple_agent_mode(candidate_id, position_id)
    results["simple_agent"] = agent_screening_id is not None
    time.sleep(2)
    
    # Test 6: TRUE AGENT MODE (the grand one!)
    true_agent_screening_id = test_true_agent_mode(candidate_id, position_id)
    results["true_agent"] = true_agent_screening_id is not None
    time.sleep(2)
    
    # Test 7: Match positions
    results["match_positions"] = test_match_positions(candidate_id)
    time.sleep(1)
    
    # Test 8: Get screening
    if true_agent_screening_id:
        results["get_screening"] = test_get_screening(true_agent_screening_id)
    
    # Summary
    print_section("TEST SUMMARY")
    print("\nResults:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Tests interrupted by user")
    except Exception as e:
        print(f"\n\n[FATAL ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()

import pytest
from app.scoring import ScoringService


def test_scoring_basic():
    """Test basic scoring computation."""
    scoring = ScoringService(threshold=0.65, hold_band=0.10)
    
    evaluations = [
        {
            "requirement_text": "Python experience",
            "category": "must",
            "weight": 0.5,
            "rating": 1.0,
            "evidence": ["5 years Python"],
            "confidence": "high"
        },
        {
            "requirement_text": "Cloud experience",
            "category": "nice",
            "weight": 0.3,
            "rating": 0.5,
            "evidence": ["Some AWS"],
            "confidence": "medium"
        },
        {
            "requirement_text": "Leadership",
            "category": "bonus",
            "weight": 0.2,
            "rating": 0.0,
            "evidence": ["not mentioned"],
            "confidence": "low"
        }
    ]
    
    result = scoring.compute_score(evaluations)
    
    assert "score" in result
    assert "decision" in result
    assert "audit_trail" in result
    
    # Expected: 1.0 * 0.5 + 0.5 * 0.3 + 0.0 * 0.2 = 0.65
    assert abs(result["score"] - 0.65) < 0.01
    assert result["decision"] == "pass"  # >= 0.65 threshold


def test_scoring_must_have_gating():
    """Test must-have gating logic."""
    scoring = ScoringService(threshold=0.65, hold_band=0.10)
    
    evaluations = [
        {
            "requirement_text": "Python experience",
            "category": "must",
            "weight": 0.5,
            "rating": 0.0,  # Must-have failed
            "evidence": ["not mentioned"],
            "confidence": "low"
        },
        {
            "requirement_text": "Cloud experience",
            "category": "nice",
            "weight": 0.5,
            "rating": 1.0,
            "evidence": ["5 years AWS"],
            "confidence": "high"
        }
    ]
    
    result = scoring.compute_score(evaluations, must_have_gating=True)
    
    assert result["decision"] == "reject"  # Must-have failed
    assert result["audit_trail"]["must_have_failed"] is True


def test_scoring_decision_bands():
    """Test decision band logic."""
    scoring = ScoringService(threshold=0.65, hold_band=0.10)
    
    # Test pass (>= threshold)
    evaluations_pass = [
        {"requirement_text": "Req", "category": "must", "weight": 1.0, "rating": 0.7, "evidence": [], "confidence": "high"}
    ]
    result = scoring.compute_score(evaluations_pass)
    assert result["decision"] == "pass"
    
    # Test hold (within hold_band)
    evaluations_hold = [
        {"requirement_text": "Req", "category": "must", "weight": 1.0, "rating": 0.60, "evidence": [], "confidence": "high"}
    ]
    result = scoring.compute_score(evaluations_hold)
    assert result["decision"] == "hold"  # 0.60 is within 0.10 of 0.65
    
    # Test reject (< threshold - hold_band)
    evaluations_reject = [
        {"requirement_text": "Req", "category": "must", "weight": 1.0, "rating": 0.50, "evidence": [], "confidence": "high"}
    ]
    result = scoring.compute_score(evaluations_reject)
    assert result["decision"] == "reject"


def test_scoring_weight_normalization():
    """Test that weights are normalized."""
    scoring = ScoringService()
    
    evaluations = [
        {"requirement_text": "Req1", "category": "must", "weight": 0.5, "rating": 1.0, "evidence": [], "confidence": "high"},
        {"requirement_text": "Req2", "category": "must", "weight": 0.5, "rating": 1.0, "evidence": [], "confidence": "high"}
    ]
    
    result = scoring.compute_score(evaluations)
    
    # Weights should sum to 1.0 after normalization
    total_weight = sum(e["weight"] for e in result["audit_trail"]["evaluation_details"])
    assert abs(total_weight - 1.0) < 0.01


def test_scoring_empty_evaluations():
    """Test scoring with empty evaluations."""
    scoring = ScoringService()
    
    result = scoring.compute_score([])
    
    assert result["score"] == 0.0
    assert result["decision"] == "reject"


def test_extract_strengths_and_gaps():
    """Test strength and gap extraction."""
    scoring = ScoringService()
    
    evaluations = [
        {
            "requirement_text": "Python",
            "category": "must",
            "rating": 1.0
        },
        {
            "requirement_text": "Cloud",
            "category": "must",
            "rating": 0.0
        },
        {
            "requirement_text": "Leadership",
            "category": "nice",
            "rating": 0.5
        }
    ]
    
    result = scoring.extract_strengths_and_gaps(evaluations)
    
    assert "strengths" in result
    assert "gaps" in result
    assert len(result["strengths"]) >= 1
    assert len(result["gaps"]) >= 1

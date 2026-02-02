import pytest
from app.schemas import (
    ScreeningResponse, RequirementBreakdown,
    PositionResponse, CandidateResponse
)
from datetime import datetime


def test_requirement_breakdown_schema():
    """Test RequirementBreakdown schema."""
    breakdown = RequirementBreakdown(
        requirement_text="Python experience",
        category="must",
        weight=0.5,
        rating=1.0,
        evidence=["5 years Python"],
        confidence="high",
        notes="Strong match"
    )
    
    assert breakdown.requirement_text == "Python experience"
    assert breakdown.category == "must"
    assert breakdown.weight == 0.5
    assert breakdown.rating == 1.0
    assert len(breakdown.evidence) == 1


def test_screening_response_schema():
    """Test ScreeningResponse schema has all required fields."""
    # This is a contract test - we're checking the schema definition
    schema = ScreeningResponse.model_json_schema()
    
    required_fields = [
        "id", "candidate_id", "position_id", "decision", "score",
        "requirement_breakdown", "strengths", "gaps",
        "clarification_questions", "suggested_interview_questions",
        "candidate_email_draft", "audit_trail", "scoring_policy"
    ]
    
    properties = schema.get("properties", {})
    
    for field in required_fields:
        assert field in properties, f"Required field '{field}' missing from schema"


def test_position_response_schema():
    """Test PositionResponse schema."""
    schema = PositionResponse.model_json_schema()
    
    required_fields = ["id", "raw_description", "structured_data", "is_open"]
    
    properties = schema.get("properties", {})
    
    for field in required_fields:
        assert field in properties, f"Required field '{field}' missing from schema"


def test_candidate_response_schema():
    """Test CandidateResponse schema."""
    schema = CandidateResponse.model_json_schema()
    
    required_fields = ["id", "structured_profile"]
    
    properties = schema.get("properties", {})
    
    for field in required_fields:
        assert field in properties, f"Required field '{field}' missing from schema"

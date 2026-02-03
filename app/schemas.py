from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class PositionCreate(BaseModel):
    raw_description: str


class PositionUpdate(BaseModel):
    is_open: Optional[bool] = None


class PositionResponse(BaseModel):
    id: str
    raw_description: str
    structured_data: Dict[str, Any]
    is_open: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    pass  # Created via file upload


class CVUploadRequest(BaseModel):
    raw_text: Optional[str] = None  # For text upload


class CandidateResponse(BaseModel):
    id: str
    cv_file_path: Optional[str]
    cv_file_type: Optional[str]
    structured_profile: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RequirementBreakdown(BaseModel):
    requirement_text: str
    category: str
    weight: float
    rating: float
    evidence: List[str]
    confidence: str
    notes: Optional[str] = None


class ScreeningResponse(BaseModel):
    id: str
    candidate_id: str
    position_id: str
    decision: str
    score: float
    requirement_breakdown: List[RequirementBreakdown]
    strengths: List[str]
    gaps: List[str]
    clarification_questions: List[str]
    suggested_interview_questions: List[str]
    candidate_email_draft: Dict[str, str]
    audit_trail: Dict[str, Any]
    scoring_policy: Dict[str, Any]
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClarificationAnswer(BaseModel):
    question: str
    answer: str


class AgentModeRequest(BaseModel):
    position_id: Optional[str] = None
    raw_job_description: Optional[str] = None
    candidate_id: Optional[str] = None
    max_iterations: int = 3
    use_true_agent: bool = False  # Use the full autonomous TrueAgent


class TrueAgentRequest(BaseModel):
    position_id: Optional[str] = None
    raw_job_description: Optional[str] = None
    candidate_id: str
    max_iterations: int = 10
    goal: Optional[str] = None  # Custom goal for the agent


class MatchPositionsResponse(BaseModel):
    matches: List[Dict[str, Any]]


class SendReviewRequest(BaseModel):
    screening_id: str
    channel: str  # email, phone, telegram, whatsapp
    custom_message: Optional[str] = None

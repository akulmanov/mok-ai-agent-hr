from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


def generate_id():
    return str(uuid.uuid4())


class Position(Base):
    __tablename__ = "positions"
    
    id = Column(String, primary_key=True, default=generate_id)
    raw_description = Column(Text, nullable=False)
    structured_data = Column(JSON)  # Extracted requirements, title, etc.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_open = Column(Boolean, default=True)
    
    screenings = relationship("Screening", back_populates="position")


class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(String, primary_key=True, default=generate_id)
    raw_cv_text = Column(Text)
    cv_file_path = Column(String)
    cv_file_type = Column(String)  # pdf, docx, txt
    structured_profile = Column(JSON)  # Extracted profile data
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    screenings = relationship("Screening", back_populates="candidate")
    clarifications = relationship("Clarification", back_populates="candidate")


class Clarification(Base):
    __tablename__ = "clarifications"
    
    id = Column(String, primary_key=True, default=generate_id)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    asked_at = Column(DateTime, server_default=func.now())
    answered_at = Column(DateTime)
    
    candidate = relationship("Candidate", back_populates="clarifications")


class Screening(Base):
    __tablename__ = "screenings"
    
    id = Column(String, primary_key=True, default=generate_id)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    position_id = Column(String, ForeignKey("positions.id"), nullable=False)
    
    # Scoring results
    decision = Column(String)  # pass, hold, reject
    score = Column(Float)
    requirement_breakdown = Column(JSON)  # List of requirement evaluations
    strengths = Column(JSON)  # List of strings
    gaps = Column(JSON)  # List of strings
    clarification_questions = Column(JSON)  # List of strings
    suggested_interview_questions = Column(JSON)  # List of strings
    candidate_email_draft = Column(JSON)  # {subject, body}
    audit_trail = Column(JSON)  # Scoring computation details
    
    # Scoring policy
    scoring_policy = Column(JSON)  # threshold, hold_band, weights, etc.
    
    # Version tracking for agent loop
    version = Column(Integer, default=1)
    parent_screening_id = Column(String, ForeignKey("screenings.id"))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    candidate = relationship("Candidate", back_populates="screenings")
    position = relationship("Position", back_populates="screenings")

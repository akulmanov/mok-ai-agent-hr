import logging
import os
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import aiofiles
from pathlib import Path

from app.database import get_db, Base, engine
from app.models import Position, Candidate, Screening
from app.agent_tools import AgentTools
from app.email_service import EmailService
from app.schemas import (
    PositionCreate, PositionResponse,
    CandidateResponse, ScreeningResponse,
    AgentModeRequest, MatchPositionsResponse,
    SendReviewRequest
)
from app.config import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)

app = FastAPI(
    title="HR Screening Agent API",
    description="Agentic HR screening system with structured evaluation and scoring",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "HR Screening Agent API",
        "version": "1.0.0",
        "endpoints": {
            "create_position": "POST /positions",
            "get_position": "GET /positions/{position_id}",
            "upload_cv": "POST /candidates/upload",
            "get_candidate": "GET /candidates/{candidate_id}",
            "run_screening": "POST /screenings",
            "get_screening": "GET /screenings/{screening_id}",
            "agent_mode": "POST /agent/screen",
            "match_positions": "POST /agent/match-positions"
        }
    }


@app.post("/positions", response_model=PositionResponse)
async def create_position(
    position: PositionCreate,
    db: Session = Depends(get_db)
):
    """Create a job posting from raw text."""
    logger.info("Creating position from raw description")
    tools = AgentTools(db)
    position_obj = tools.create_position(position.raw_description)
    return position_obj


@app.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    db: Session = Depends(get_db)
):
    """Get position by ID."""
    tools = AgentTools(db)
    position = tools.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@app.post("/candidates/upload", response_model=CandidateResponse)
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload CV and create candidate."""
    logger.info(f"Uploading CV: {file.filename}")
    
    # Determine file type
    file_type = None
    if file.filename:
        ext = Path(file.filename).suffix.lower().lstrip('.')
        if ext in ['pdf', 'docx', 'txt']:
            file_type = ext
    
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый тип файла. Поддерживаются: PDF, DOCX, TXT"
        )
    
    # Save file with unique name to avoid conflicts
    file_ext = Path(file.filename).suffix if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Create candidate
    tools = AgentTools(db)
    candidate = await tools.create_candidate_from_file(file_path, file_type)
    
    return candidate


@app.get("/candidates")
async def list_candidates(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all candidates."""
    query = db.query(Candidate)
    candidates = query.order_by(Candidate.created_at.desc()).limit(limit).all()
    return candidates


@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get candidate by ID."""
    tools = AgentTools(db)
    candidate = tools.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Кандидат не найден")
    return candidate


@app.post("/screenings", response_model=ScreeningResponse)
async def run_screening(
    candidate_id: str,
    position_id: str,
    db: Session = Depends(get_db)
):
    """Run screening evaluation."""
    logger.info(f"Running screening: candidate={candidate_id}, position={position_id}")
    tools = AgentTools(db)
    
    try:
        screening = tools.run_evaluation(candidate_id, position_id)
        return screening
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error running screening: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.get("/screenings/{screening_id}", response_model=ScreeningResponse)
async def get_screening(
    screening_id: str,
    db: Session = Depends(get_db)
):
    """Get screening by ID."""
    screening = db.query(Screening).filter(Screening.id == screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Отбор не найден")
    return screening


@app.post("/agent/screen", response_model=ScreeningResponse)
async def agent_mode(
    request: AgentModeRequest,
    db: Session = Depends(get_db)
):
    """
    Agent mode: can accept raw job description or position_id,
    and CV file or candidate_id. Runs agent loop.
    """
    logger.info("Running agent mode screening")
    tools = AgentTools(db)
    
    # Resolve position
    if request.position_id:
        position_id = request.position_id
    elif request.raw_job_description:
        position = tools.create_position(request.raw_job_description)
        position_id = position.id
    else:
        raise HTTPException(
            status_code=400,
            detail="Either position_id or raw_job_description must be provided"
        )
    
    # Resolve candidate
    if not request.candidate_id:
        raise HTTPException(
            status_code=400,
            detail="candidate_id must be provided (file upload not supported in agent mode, use /candidates/upload first)"
        )
    
    candidate_id = request.candidate_id
    
    # Run agent loop
    try:
        screening = tools.run_agent_loop(
            candidate_id,
            position_id,
            max_iterations=request.max_iterations
        )
        return screening
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in agent mode: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.post("/agent/match-positions", response_model=MatchPositionsResponse)
async def match_positions(
    candidate_id: str,
    top_n: int = 5,
    db: Session = Depends(get_db)
):
    """Match candidate against all open positions and return top N."""
    logger.info(f"Matching candidate {candidate_id} against open positions")
    tools = AgentTools(db)
    
    try:
        matches = tools.find_matching_positions(candidate_id, top_n=top_n)
        return MatchPositionsResponse(matches=matches)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error matching positions: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.get("/screenings")
async def list_screenings(
    candidate_id: Optional[str] = None,
    position_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List screenings with optional filters."""
    query = db.query(Screening)
    
    if candidate_id:
        query = query.filter(Screening.candidate_id == candidate_id)
    if position_id:
        query = query.filter(Screening.position_id == position_id)
    
    screenings = query.order_by(Screening.created_at.desc()).limit(limit).all()
    return screenings


@app.post("/screenings/{screening_id}/send-review")
async def send_review_result(
    screening_id: str,
    request: SendReviewRequest,
    db: Session = Depends(get_db)
):
    """Send review result to candidate via specified channel."""
    logger.info(f"Sending review result for screening {screening_id} via {request.channel}")
    
    tools = AgentTools(db)
    screening = tools.get_screening(screening_id)
    if not screening:
        raise HTTPException(status_code=404, detail="Отбор не найден")
    
    candidate = tools.get_candidate(screening.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Кандидат не найден")
    
    # Get available channels
    email_service = EmailService()
    channels = email_service.get_available_channels(candidate.structured_profile)
    
    # Check if requested channel is available
    channel_value = channels.get(request.channel)
    if not channel_value:
        available = [k for k, v in channels.items() if v]
        raise HTTPException(
            status_code=400,
            detail=f"Канал '{request.channel}' недоступен. Доступные каналы: {', '.join(available) if available else 'нет'}"
        )
    
    # Prepare message
    candidate_name = candidate.structured_profile.get("name") if candidate.structured_profile else None
    email_draft = screening.candidate_email_draft or {}
    subject = email_draft.get("subject", "Результат отбора")
    body = request.custom_message or email_draft.get("body", "Спасибо за вашу заявку.")
    
    # Send via appropriate channel
    success = False
    if request.channel == "email":
        success = await email_service.send_review_result(
            to_email=channel_value,
            candidate_name=candidate_name,
            subject=subject,
            body=body
        )
    elif request.channel == "phone":
        logger.info(f"Phone sending not implemented yet. Would send to {channel_value}")
        return {"success": False, "message": "Отправка по телефону пока не реализована"}
    elif request.channel == "telegram":
        logger.info(f"Telegram sending not implemented yet. Would send to {channel_value}")
        return {"success": False, "message": "Отправка в Telegram пока не реализована"}
    elif request.channel == "whatsapp":
        logger.info(f"WhatsApp sending not implemented yet. Would send to {channel_value}")
        return {"success": False, "message": "Отправка в WhatsApp пока не реализована"}
    else:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый канал: {request.channel}")
    
    if success:
        return {
            "success": True,
            "message": f"Результат отправлен кандидату через {request.channel}",
            "channel": request.channel,
            "recipient": channel_value
        }
    else:
        raise HTTPException(status_code=500, detail="Не удалось отправить сообщение")


@app.get("/candidates/{candidate_id}/channels")
async def get_candidate_channels(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Get available communication channels for a candidate."""
    tools = AgentTools(db)
    candidate = tools.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Кандидат не найден")
    
    email_service = EmailService()
    channels = email_service.get_available_channels(candidate.structured_profile)
    
    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate.structured_profile.get("name") if candidate.structured_profile else None,
        "channels": channels,
        "available_channels": [k for k, v in channels.items() if v]
    }

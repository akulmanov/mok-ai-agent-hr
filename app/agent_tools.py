import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import Position, Candidate, Screening, Clarification
from app.llm_service import LLMService
from app.scoring import ScoringService
from app.cv_parser import CVParser
from app.true_agent import TrueAgent
from pathlib import Path
import math

logger = logging.getLogger(__name__)

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    if denom == 0.0:
        return -1.0
    return dot / denom

def _build_position_match_text(position: Position) -> str:
    sd = position.structured_data or {}
    title = sd.get("title", "") or ""
    summary = sd.get("summary", "") or ""
    reqs = sd.get("requirements", []) or []
    # Keep it compact; embeddings work well with concise, relevant text.
    req_lines = []
    for r in reqs[:25]:
        text = (r or {}).get("text", "")
        cat = (r or {}).get("category", "")
        if text:
            req_lines.append(f"[{cat}] {text}".strip())
    return "\n".join([f"TITLE: {title}", f"SUMMARY: {summary}", "REQUIREMENTS:", *req_lines]).strip()

def _build_candidate_match_text(candidate: Candidate) -> str:
    prof = candidate.structured_profile or {}
    summary = prof.get("summary", "") or ""
    skills = prof.get("skills", []) or []
    exp = prof.get("experience", []) or []
    exp_lines = []
    for e in exp[:10]:
        role = (e or {}).get("role", "")
        company = (e or {}).get("company", "")
        desc = (e or {}).get("description", "")
        line = " | ".join([p for p in [role, company] if p])
        if desc:
            line = f"{line}: {desc}" if line else desc
        if line:
            exp_lines.append(line)
    skills_line = ", ".join([s for s in skills[:40] if isinstance(s, str)])
    # Use a slice of raw text as extra signal (but keep token/cost bounded)
    raw = (candidate.raw_cv_text or "")[:2000]
    return "\n".join([
        f"SUMMARY: {summary}",
        f"SKILLS: {skills_line}",
        "EXPERIENCE:",
        *exp_lines,
        "RAW:",
        raw
    ]).strip()


class AgentTools:
    """Agentic tools for the HR screening system."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()
        self.cv_parser = CVParser()
        self.scoring = ScoringService()
    
    def create_position(self, raw_description: str) -> Position:
        """Create a position from raw job description."""
        logger.info("Создание вакансии из описания")
        
        # Extract structured data
        structured_data = self.llm.extract_job_requirements(raw_description)

        # Pre-compute embedding for matching (store inside JSON to avoid DB migrations)
        try:
            match_text = _build_position_match_text(Position(raw_description=raw_description, structured_data=structured_data, is_open=True))
            structured_data["_match_text"] = match_text
            structured_data["_match_embedding"] = self.llm.embed_text(match_text)
        except Exception as e:
            logger.warning(f"Не удалось вычислить embedding для вакансии: {e}")
        
        position = Position(
            raw_description=raw_description,
            structured_data=structured_data,
            is_open=True
        )
        
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        
        logger.info(f"Создана вакансия {position.id}")
        return position
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID."""
        return self.db.query(Position).filter(Position.id == position_id).first()
    
    async def create_candidate_from_file(
        self,
        file_path: str,
        file_type: Optional[str] = None
    ) -> Candidate:
        """Create candidate from CV file."""
        logger.info(f"Создание кандидата из файла: {file_path}")
        
        # Parse CV
        cv_text = await self.cv_parser.parse_file(file_path, file_type)
        
        # Extract structured profile
        structured_profile = self.llm.extract_candidate_profile(cv_text)

        # Pre-compute embedding for matching (store inside JSON to avoid DB migrations)
        try:
            # We'll temporarily create a Candidate-like container by passing raw text + profile after Candidate creation below.
            structured_profile["_match_text"] = ""  # filled after candidate instantiation
        except Exception:
            pass
        
        # Determine file type
        if file_type is None:
            file_type = Path(file_path).suffix.lower().lstrip('.')
        
        candidate = Candidate(
            raw_cv_text=cv_text,
            cv_file_path=file_path,
            cv_file_type=file_type,
            structured_profile=structured_profile
        )

        try:
            match_text = _build_candidate_match_text(candidate)
            prof = candidate.structured_profile or {}
            prof["_match_text"] = match_text
            prof["_match_embedding"] = self.llm.embed_text(match_text)
            candidate.structured_profile = prof
        except Exception as e:
            logger.warning(f"Не удалось вычислить embedding для кандидата: {e}")
        
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        
        logger.info(f"Создан кандидат {candidate.id}")
        return candidate
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID."""
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    def run_evaluation(
        self,
        candidate_id: str,
        position_id: str,
        version: int = 1,
        parent_screening_id: Optional[str] = None
    ) -> Screening:
        """Run evaluation and create screening record."""
        logger.info(f"Запуск оценки: кандидат={candidate_id}, вакансия={position_id}")
        
        candidate = self.get_candidate(candidate_id)
        position = self.get_position(position_id)
        
        if not candidate or not position:
            raise ValueError("Кандидат или вакансия не найдены")
        
        # Get requirements
        requirements = position.structured_data.get("requirements", [])
        
        # Evaluate requirements
        evaluations = self.llm.evaluate_requirements(
            requirements,
            candidate.structured_profile,
            candidate.raw_cv_text
        )
        
        # Compute score
        score_result = self.scoring.compute_score(evaluations, must_have_gating=True)
        
        # Extract strengths and gaps
        strengths_gaps = self.scoring.extract_strengths_and_gaps(evaluations)
        
        # Generate clarification questions ТОЛЬКО если решение "на рассмотрении"
        # Для явного "проходите" или "не подходите" не мучаем кандидата вопросами.
        clarification_questions: List[str] = []
        if score_result["decision"] == "hold":
            clarification_questions = self.llm.generate_clarification_questions(
                requirements,
                candidate.structured_profile,
                evaluations
            )
        
        # Generate interview questions
        interview_questions = self.llm.generate_interview_questions(
            requirements,
            strengths_gaps["strengths"],
            strengths_gaps["gaps"]
        )
        
        # Generate email draft
        candidate_name = candidate.structured_profile.get("name")
        email_draft = self.llm.generate_email_draft(
            candidate_name,
            score_result["decision"],
            score_result["score"],
            strengths_gaps["strengths"],
            strengths_gaps["gaps"]
        )
        
        # Create screening record
        screening = Screening(
            candidate_id=candidate_id,
            position_id=position_id,
            decision=score_result["decision"],
            score=score_result["score"],
            requirement_breakdown=evaluations,
            strengths=strengths_gaps["strengths"],
            gaps=strengths_gaps["gaps"],
            clarification_questions=clarification_questions,
            suggested_interview_questions=interview_questions,
            candidate_email_draft=email_draft,
            audit_trail=score_result["audit_trail"],
            scoring_policy={
                "threshold": self.scoring.threshold,
                "hold_band": self.scoring.hold_band,
                "must_have_gating": True
            },
            version=version,
            parent_screening_id=parent_screening_id
        )
        
        self.db.add(screening)
        self.db.commit()
        self.db.refresh(screening)
        
        logger.info(f"Создан отбор {screening.id} с решением: {score_result['decision']}")
        return screening
    
    def add_clarification_answer(
        self,
        candidate_id: str,
        question: str,
        answer: str
    ) -> Clarification:
        """Add clarification answer and update candidate profile if needed."""
        clarification = Clarification(
            candidate_id=candidate_id,
            question=question,
            answer=answer
        )
        
        self.db.add(clarification)
        self.db.commit()
        self.db.refresh(clarification)
        
        # Optionally update candidate profile with new info
        # For now, we'll just store the clarification
        
        return clarification
    
    def run_agent_loop(
        self,
        candidate_id: str,
        position_id: str,
        max_iterations: int = 3,
        use_true_agent: bool = False
    ) -> Screening:
        """
        Run agent loop: evaluate, ask questions if needed, re-evaluate.
        
        Args:
            candidate_id: ID of the candidate
            position_id: ID of the position
            max_iterations: Maximum number of iterations
            use_true_agent: If True, use the TrueAgent with full autonomous capabilities
        """
        if use_true_agent:
            logger.info("🤖 Использование TrueAgent с полными автономными возможностями")
            agent = TrueAgent(self.db, self.llm)
            return agent.run_autonomous_screening(
                candidate_id=candidate_id,
                position_id=position_id,
                max_iterations=max_iterations
            )
        
        # Legacy simple agent loop
        logger.info(f"Запуск простого цикла агента: кандидат={candidate_id}, вакансия={position_id}")
        
        screening = None
        parent_screening_id = None
        
        for iteration in range(1, max_iterations + 1):
            # Run evaluation
            screening = self.run_evaluation(
                candidate_id,
                position_id,
                version=iteration,
                parent_screening_id=parent_screening_id
            )
            
            # Check if clarification is needed
            if not screening.clarification_questions or len(screening.clarification_questions) == 0:
                logger.info("Уточнения не требуются, цикл агента завершен")
                break
            
            # If we have questions but reached max iterations, stop
            if iteration >= max_iterations:
                logger.info(f"Достигнуто максимальное количество итераций ({max_iterations}), остановка цикла агента")
                break
            
            # In a real system, we'd wait for user answers here
            # For now, we'll just mark that questions were generated
            logger.info(f"Итерация {iteration}: Сгенерировано {len(screening.clarification_questions)} уточняющих вопросов")
            parent_screening_id = screening.id
        
        return screening
    
    def get_screening(self, screening_id: str) -> Optional[Screening]:
        """Get screening by ID."""
        return self.db.query(Screening).filter(Screening.id == screening_id).first()
    
    def find_matching_positions(
        self,
        candidate_id: str,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find top N matching positions for a candidate.
        Uses fast embedding-based retrieval to select top-N positions, then runs full evaluation only on those.
        """
        candidate = self.get_candidate(candidate_id)
        if not candidate:
            raise ValueError("Кандидат не найден")

        # Retrieve top positions (fast)
        positions_to_check = self.retrieve_top_positions_for_candidate(candidate_id, top_n=top_n)
        if not positions_to_check:
            return []

        # Evaluate only retrieved positions (expensive)
        matches = []
        for position in positions_to_check:
            try:
                screening = self.run_evaluation(candidate_id, position.id, version=1)
                matches.append({
                    "position_id": position.id,
                    "position_title": position.structured_data.get("title", "Unknown"),
                    "score": screening.score,
                    "decision": screening.decision,
                    "screening_id": screening.id
                })
            except Exception as e:
                logger.error(f"Ошибка при оценке вакансии {position.id}: {e}")
                continue
        
        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        return matches[:top_n]

    def retrieve_top_positions_for_candidate(self, candidate_id: str, top_n: int = 5) -> List[Position]:
        """
        Fast retrieval: compute cosine similarity between candidate embedding and each open position embedding.
        Embeddings are cached inside JSON fields:
          - Candidate.structured_profile['_match_embedding']
          - Position.structured_data['_match_embedding']
        """
        candidate = self.get_candidate(candidate_id)
        if not candidate:
            raise ValueError("Кандидат не найден")

        open_positions = self.db.query(Position).filter(Position.is_open == True).all()
        if not open_positions:
            return []

        # Ensure candidate embedding exists
        prof = candidate.structured_profile or {}
        cand_emb = prof.get("_match_embedding")
        if not cand_emb:
            match_text = _build_candidate_match_text(candidate)
            prof["_match_text"] = match_text
            prof["_match_embedding"] = self.llm.embed_text(match_text)
            candidate.structured_profile = prof
            self.db.commit()
            cand_emb = prof["_match_embedding"]

        scored: List[tuple[float, Position]] = []
        for pos in open_positions:
            sd = pos.structured_data or {}
            pos_emb = sd.get("_match_embedding")
            if not pos_emb:
                match_text = _build_position_match_text(pos)
                sd["_match_text"] = match_text
                sd["_match_embedding"] = self.llm.embed_text(match_text)
                pos.structured_data = sd
                self.db.commit()
                pos_emb = sd["_match_embedding"]

            sim = _cosine_similarity(cand_emb, pos_emb)
            scored.append((sim, pos))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:top_n]]

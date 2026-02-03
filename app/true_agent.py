"""
True Agent - Grand orchestrator for autonomous HR screening agent.
Implements full agentic capabilities: reasoning, planning, tool selection, and adaptation.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.agent_memory import AgentMemory
from app.agent_planner import AgentPlanner
from app.agent_reasoner import AgentReasoner
from app.tool_registry import ToolRegistry
from app.llm_service import LLMService
from app.models import Candidate, Position, Screening, Clarification
from app.scoring import ScoringService

logger = logging.getLogger(__name__)


class TrueAgent:
    """
    True autonomous agent for HR screening.
    Implements:
    - Autonomous reasoning (ReAct pattern)
    - Strategic planning
    - Dynamic tool selection
    - Memory management
    - Self-reflection and adaptation
    """
    
    def __init__(self, db: Session, llm_service: Optional[LLMService] = None):
        self.db = db
        self.llm = llm_service or LLMService()
        self.scoring = ScoringService()
        
        # Core components
        self.memory = AgentMemory()
        self.planner = AgentPlanner(self.llm)
        self.reasoner = AgentReasoner(self.llm)
        self.tools = ToolRegistry()
        
        # Register all available tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools with the registry."""
        
        # Evaluation tool
        self.tools.register_tool(
            name="evaluate",
            func=self._tool_evaluate,
            description="Evaluate candidate against position requirements. Returns screening with score and decision.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "position_id": "string - ID of the position"
            },
            category="evaluation"
        )
        
        # Clarification questions tool
        self.tools.register_tool(
            name="ask_clarification",
            func=self._tool_ask_clarification,
            description="Generate clarification questions for unclear requirements. Returns list of questions.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "position_id": "string - ID of the position",
                "screening_id": "string - ID of the screening to base questions on"
            },
            category="information_gathering"
        )
        
        # Answer collection tool
        self.tools.register_tool(
            name="collect_answers",
            func=self._tool_collect_answers,
            description="Collect answers to clarification questions and update candidate profile.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "answers": "dict - Dictionary mapping question to answer"
            },
            category="information_gathering"
        )
        
        # Process answers tool (extracts structured info from answers)
        self.tools.register_tool(
            name="process_answers",
            func=self._tool_process_answers,
            description="Process answers to extract structured information and update candidate profile intelligently.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "answers": "dict - Dictionary mapping question to answer",
                "screening_id": "string - ID of the screening that generated the questions"
            },
            category="information_gathering"
        )
        
        # Profile update tool
        self.tools.register_tool(
            name="update_profile",
            func=self._tool_update_profile,
            description="Update candidate profile with new information from answers.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "new_info": "dict - New information to add to profile"
            },
            category="data_management"
        )
        
        # Re-evaluation tool
        self.tools.register_tool(
            name="reevaluate",
            func=self._tool_reevaluate,
            description="Re-evaluate candidate after profile update. Returns new screening.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "position_id": "string - ID of the position",
                "previous_screening_id": "string - ID of previous screening"
            },
            category="evaluation"
        )
        
        # Decision finalization tool
        self.tools.register_tool(
            name="finalize_decision",
            func=self._tool_finalize_decision,
            description="Finalize screening decision with confidence check. Returns final screening.",
            parameters={
                "screening_id": "string - ID of the screening to finalize",
                "force_decision": "bool - Force decision even if confidence is low (default: False)"
            },
            category="decision"
        )
        
        # Candidate analysis tool
        self.tools.register_tool(
            name="analyze_candidate",
            func=self._tool_analyze_candidate,
            description="Deep analysis of candidate profile. Returns detailed analysis.",
            parameters={
                "candidate_id": "string - ID of the candidate"
            },
            category="analysis"
        )
        
        # Position analysis tool
        self.tools.register_tool(
            name="analyze_position",
            func=self._tool_analyze_position,
            description="Deep analysis of position requirements. Returns detailed analysis.",
            parameters={
                "position_id": "string - ID of the position"
            },
            category="analysis"
        )
        
        # Comparison tool
        self.tools.register_tool(
            name="compare",
            func=self._tool_compare,
            description="Compare candidate against multiple positions or other candidates.",
            parameters={
                "candidate_id": "string - ID of the candidate",
                "position_ids": "list - List of position IDs to compare against (optional)"
            },
            category="analysis"
        )
        
        logger.info(f"Registered {len(self.tools.tools)} tools")
    
    # Tool implementations
    def _tool_evaluate(self, candidate_id: str, position_id: str) -> Dict[str, Any]:
        """Evaluate candidate against position."""
        from app.agent_tools import AgentTools
        tools = AgentTools(self.db)
        screening = tools.run_evaluation(candidate_id, position_id)
        return {
            "success": True,
            "screening_id": screening.id,
            "score": screening.score,
            "decision": screening.decision,
            "summary": f"Evaluation complete: {screening.decision} (score: {screening.score:.2f})"
        }
    
    def _tool_ask_clarification(self, candidate_id: str, position_id: str, screening_id: str) -> Dict[str, Any]:
        """Generate clarification questions."""
        screening = self.db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            return {"success": False, "error": "Screening not found", "questions": []}
        
        questions = screening.clarification_questions or []
        return {
            "success": True,
            "questions": questions,
            "count": len(questions),
            "summary": f"Generated {len(questions)} clarification questions"
        }
    
    def _tool_collect_answers(self, candidate_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """Collect answers to clarification questions."""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        
        # Store answers as clarifications
        for question, answer in answers.items():
            clarification = Clarification(
                candidate_id=candidate_id,
                question=question,
                answer=answer
            )
            self.db.add(clarification)
        
        self.db.commit()
        
        return {
            "success": True,
            "answers_collected": len(answers),
            "summary": f"Collected {len(answers)} answers"
        }
    
    def _tool_process_answers(self, candidate_id: str, answers: Dict[str, str], screening_id: str) -> Dict[str, Any]:
        """Process answers using LLM to extract structured information and update profile."""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        
        # Use LLM to extract structured information from answers
        system_prompt = """Вы извлекаете структурированную информацию из ответов кандидата на уточняющие вопросы.
Проанализируйте ответы и извлеките релевантную информацию для обновления профиля кандидата.
Верните JSON объект с извлеченной информацией, которую можно добавить в structured_profile."""
        
        answers_str = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()])
        profile_str = json.dumps(candidate.structured_profile or {}, indent=2, ensure_ascii=False)
        
        user_prompt = f"""ТЕКУЩИЙ ПРОФИЛЬ:
{profile_str}

ОТВЕТЫ КАНДИДАТА:
{answers_str}

Извлеките структурированную информацию из ответов и верните JSON объект для обновления профиля.
Верните только валидный JSON."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm._call_llm(messages, response_format={"type": "json_object"})
            new_info = json.loads(response)
            
            # Merge into profile
            profile = candidate.structured_profile or {}
            profile.update(new_info)
            candidate.structured_profile = profile
            
            # Store answers as clarifications
            for question, answer in answers.items():
                clarification = Clarification(
                    candidate_id=candidate_id,
                    question=question,
                    answer=answer
                )
                self.db.add(clarification)
            
            self.db.commit()
            self.db.refresh(candidate)
            
            return {
                "success": True,
                "answers_processed": len(answers),
                "updated_fields": list(new_info.keys()),
                "summary": f"Processed {len(answers)} answers and updated {len(new_info)} profile fields"
            }
        except Exception as e:
            logger.error(f"Error processing answers: {e}")
            return {"success": False, "error": str(e)}
    
    def _tool_update_profile(self, candidate_id: str, new_info: Dict[str, Any]) -> Dict[str, Any]:
        """Update candidate profile with new information."""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        
        # Merge new info into structured profile
        profile = candidate.structured_profile or {}
        profile.update(new_info)
        candidate.structured_profile = profile
        
        self.db.commit()
        self.db.refresh(candidate)
        
        return {
            "success": True,
            "updated_fields": list(new_info.keys()),
            "summary": f"Updated profile with {len(new_info)} fields"
        }
    
    def _tool_reevaluate(self, candidate_id: str, position_id: str, previous_screening_id: str) -> Dict[str, Any]:
        """Re-evaluate candidate after profile update."""
        from app.agent_tools import AgentTools
        tools = AgentTools(self.db)
        
        # Get previous screening to determine version
        prev_screening = self.db.query(Screening).filter(Screening.id == previous_screening_id).first()
        version = (prev_screening.version if prev_screening else 0) + 1
        
        screening = tools.run_evaluation(
            candidate_id,
            position_id,
            version=version,
            parent_screening_id=previous_screening_id
        )
        
        return {
            "success": True,
            "screening_id": screening.id,
            "score": screening.score,
            "decision": screening.decision,
            "version": version,
            "summary": f"Re-evaluation complete: {screening.decision} (score: {screening.score:.2f})"
        }
    
    def _tool_finalize_decision(self, screening_id: str, force_decision: bool = False) -> Dict[str, Any]:
        """Finalize screening decision."""
        screening = self.db.query(Screening).filter(Screening.id == screening_id).first()
        if not screening:
            return {"success": False, "error": "Screening not found"}
        
        # Check confidence (based on score and uncertainties)
        confidence = 0.8 if screening.score >= 0.7 else 0.5
        if screening.clarification_questions and len(screening.clarification_questions) > 0:
            confidence -= 0.2
        
        if not force_decision and confidence < 0.6:
            return {
                "success": False,
                "error": "Confidence too low",
                "confidence": confidence,
                "suggestion": "Collect more information first"
            }
        
        return {
            "success": True,
            "screening_id": screening.id,
            "decision": screening.decision,
            "score": screening.score,
            "confidence": confidence,
            "summary": f"Decision finalized: {screening.decision}"
        }
    
    def _tool_analyze_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """Deep analysis of candidate."""
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"success": False, "error": "Candidate not found"}
        
        profile = candidate.structured_profile or {}
        return {
            "success": True,
            "candidate_id": candidate_id,
            "profile": profile,
            "summary": f"Analyzed candidate: {profile.get('name', 'Unknown')}"
        }
    
    def _tool_analyze_position(self, position_id: str) -> Dict[str, Any]:
        """Deep analysis of position."""
        position = self.db.query(Position).filter(Position.id == position_id).first()
        if not position:
            return {"success": False, "error": "Position not found"}
        
        return {
            "success": True,
            "position_id": position_id,
            "structured_data": position.structured_data,
            "summary": f"Analyzed position: {position.structured_data.get('title', 'Unknown')}"
        }
    
    def _tool_compare(self, candidate_id: str, position_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compare candidate against positions."""
        from app.agent_tools import AgentTools
        tools = AgentTools(self.db)
        
        if position_ids:
            matches = []
            for pos_id in position_ids:
                try:
                    screening = tools.run_evaluation(candidate_id, pos_id)
                    matches.append({
                        "position_id": pos_id,
                        "score": screening.score,
                        "decision": screening.decision
                    })
                except Exception as e:
                    logger.error(f"Error comparing with position {pos_id}: {e}")
        else:
            matches = tools.find_matching_positions(candidate_id, top_n=5)
        
        return {
            "success": True,
            "matches": matches,
            "count": len(matches),
            "summary": f"Compared against {len(matches)} positions"
        }
    
    def run_autonomous_screening(
        self,
        candidate_id: str,
        position_id: str,
        max_iterations: int = 10,
        goal: Optional[str] = None
    ) -> Screening:
        """
        Run autonomous agent screening with full reasoning, planning, and adaptation.
        
        This is the main entry point for the true agent.
        """
        logger.info(f"🤖 Starting autonomous agent screening: candidate={candidate_id}, position={position_id}")
        
        # Set goal
        if not goal:
            goal = f"Evaluate candidate {candidate_id} for position {position_id} with high confidence"
        self.memory.set_goal(goal)
        
        # Initialize context
        context = {
            "candidate_id": candidate_id,
            "position_id": position_id,
            "iterations": 0,
            "completed_steps": [],
            "current_screening_id": None
        }
        self.memory.update_context("candidate_id", candidate_id)
        self.memory.update_context("position_id", position_id)
        
        # Create initial plan
        plan = self.planner.create_plan(goal, context)
        self.memory.update_context("plan", plan)
        
        # Main agent loop
        final_screening = None
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            context["iterations"] = iterations
            
            logger.info(f"🔄 Agent iteration {iterations}/{max_iterations}")
            
            # Get memory summary
            memory_summary = self.memory.get_memory_summary()
            recent_obs = self.memory.get_recent_observations(5)
            recent_actions = self.memory.get_recent_actions(5)
            
            # Reason about next action
            reasoning_result = self.reasoner.reason_next_action(
                goal=goal,
                context=context,
                available_tools=self.tools.get_tools_for_reasoning(),
                memory_summary=memory_summary,
                recent_observations=recent_obs,
                recent_actions=recent_actions
            )
            
            # Record reasoning
            self.memory.add_observation({
                "type": "reasoning",
                "thought": reasoning_result.get("thought"),
                "action": reasoning_result.get("action"),
                "confidence": reasoning_result.get("confidence", 0.0)
            })
            
            # Execute action
            action_name = reasoning_result.get("action")
            action_input = reasoning_result.get("action_input", {})
            
            # Ensure required context parameters are in action_input
            if "candidate_id" not in action_input:
                action_input["candidate_id"] = candidate_id
            if "position_id" not in action_input and "position_id" in context:
                action_input["position_id"] = position_id
            
            logger.info(f"⚙️  Executing action: {action_name} with {action_input}")
            
            try:
                result = self.tools.execute_tool(action_name, **action_input)
                
                # Record action and result
                self.memory.add_action(
                    {
                        "type": action_name,
                        "input": action_input
                    },
                    result
                )
                
                # Update context with results
                if "screening_id" in result:
                    context["current_screening_id"] = result["screening_id"]
                    final_screening_id = result["screening_id"]
                    final_screening = self.db.query(Screening).filter(Screening.id == final_screening_id).first()
                
                # Reflect on result
                reflection = self.reasoner.reflect_on_result(
                    action=reasoning_result,
                    result=result,
                    goal=goal,
                    context=context
                )
                
                # Update memory based on reflection
                for obs in reflection.get("observations", []):
                    self.memory.add_observation({
                        "type": "observation",
                        "summary": obs
                    })
                
                for unc in reflection.get("uncertainties", []):
                    self.memory.add_uncertainty(unc)
                
                # Update confidence
                current_confidence = self.memory.get_current_confidence()
                new_confidence = max(0.0, min(1.0, current_confidence + reflection.get("confidence_delta", 0.0)))
                self.memory.update_confidence(new_confidence, reflection.get("reasoning", "From reflection"))
                
                # Check if should stop
                uncertainties = self.memory.get_unresolved_uncertainties()
                stop_decision = self.reasoner.should_stop(
                    goal=goal,
                    confidence=new_confidence,
                    uncertainties=[u["text"] for u in uncertainties],
                    iterations=iterations,
                    max_iterations=max_iterations
                )
                
                if stop_decision["should_stop"]:
                    logger.info(f"🛑 Agent stopping: {stop_decision['reason']}")
                    break
                
                # Adapt plan if needed
                if reflection.get("should_continue", True):
                    plan = self.planner.adapt_plan(plan, recent_obs, action_name)
                    self.memory.update_context("plan", plan)
                
            except Exception as e:
                logger.error(f"❌ Error executing action {action_name}: {e}")
                self.memory.add_observation({
                    "type": "error",
                    "summary": f"Error in {action_name}: {str(e)}"
                })
                # Continue with next iteration
        
        # Finalize
        if not final_screening:
            # If no screening was created, create one now
            from app.agent_tools import AgentTools
            tools = AgentTools(self.db)
            final_screening = tools.run_evaluation(candidate_id, position_id)
        
        logger.info(f"✅ Autonomous agent screening complete: {final_screening.id}")
        return final_screening
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get the current state of the agent (memory, context, etc.)."""
        return {
            "memory": self.memory.get_memory_summary(),
            "recent_observations": [
                {
                    "type": obs.get("type"),
                    "summary": obs.get("summary", str(obs))
                }
                for obs in self.memory.get_recent_observations(10)
            ],
            "recent_actions": [
                {
                    "action": act.get("action", {}).get("type"),
                    "result_summary": act.get("result", {}).get("summary", "executed")
                }
                for act in self.memory.get_recent_actions(10)
            ],
            "unresolved_uncertainties": [
                u["text"] for u in self.memory.get_unresolved_uncertainties()
            ],
            "confidence": self.memory.get_current_confidence(),
            "available_tools": len(self.tools.tools)
        }

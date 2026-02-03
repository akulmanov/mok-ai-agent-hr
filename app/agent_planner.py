"""
Agent Planner - Goal decomposition and strategic planning.
"""
import logging
from typing import Dict, List, Any, Optional
from app.llm_service import LLMService
import json

logger = logging.getLogger(__name__)


class AgentPlanner:
    """
    Sophisticated planning system that decomposes goals into actionable steps.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    def create_plan(
        self,
        goal: str,
        context: Dict[str, Any],
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a strategic plan to achieve the goal.
        
        Returns:
            {
                "goal": str,
                "sub_goals": List[str],
                "steps": List[Dict],
                "estimated_iterations": int,
                "strategy": str
            }
        """
        logger.info(f"Creating plan for goal: {goal}")
        
        system_prompt = """Вы - стратегический планировщик для HR агента. Ваша задача - разбить цель на подцели и шаги.

Создайте детальный план, который:
1. Разбивает главную цель на логические подцели
2. Определяет последовательность шагов для каждой подцели
3. Учитывает ограничения и контекст
4. Предполагает количество итераций
5. Выбирает стратегию (консервативная, агрессивная, адаптивная)

Верните JSON объект с:
- goal: Главная цель
- sub_goals: Список подцелей
- steps: Массив шагов, каждый с:
  - step_id: Уникальный ID
  - sub_goal: К какой подцели относится
  - action: Что нужно сделать
  - tool: Какой инструмент использовать
  - dependencies: Какие шаги должны быть выполнены до этого
  - expected_outcome: Ожидаемый результат
- estimated_iterations: Оценка количества итераций
- strategy: "conservative" | "aggressive" | "adaptive"
- risk_factors: Список потенциальных рисков"""
        
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        constraints_str = "\n".join(constraints) if constraints else "Нет особых ограничений"
        
        user_prompt = f"""Создайте план для достижения цели:

ЦЕЛЬ: {goal}

КОНТЕКСТ:
{context_str}

ОГРАНИЧЕНИЯ:
{constraints_str}

Верните только валидный JSON."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm._call_llm(messages, response_format={"type": "json_object"})
        
        try:
            plan = json.loads(response)
            # Validate and normalize plan structure
            if "steps" not in plan:
                plan["steps"] = []
            if "sub_goals" not in plan:
                plan["sub_goals"] = []
            if "estimated_iterations" not in plan:
                plan["estimated_iterations"] = 5
            if "strategy" not in plan:
                plan["strategy"] = "adaptive"
            
            logger.info(f"Created plan with {len(plan.get('steps', []))} steps")
            return plan
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {e}")
            # Return a default plan
            return self._create_default_plan(goal, context)
    
    def _create_default_plan(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple default plan if LLM fails."""
        return {
            "goal": goal,
            "sub_goals": ["Evaluate candidate", "Resolve uncertainties", "Make decision"],
            "steps": [
                {
                    "step_id": "1",
                    "sub_goal": "Evaluate candidate",
                    "action": "Run initial evaluation",
                    "tool": "evaluate",
                    "dependencies": [],
                    "expected_outcome": "Initial score and evaluation"
                },
                {
                    "step_id": "2",
                    "sub_goal": "Resolve uncertainties",
                    "action": "Generate clarification questions if needed",
                    "tool": "ask_clarification",
                    "dependencies": ["1"],
                    "expected_outcome": "List of questions or empty list"
                },
                {
                    "step_id": "3",
                    "sub_goal": "Make decision",
                    "action": "Finalize decision based on evaluation",
                    "tool": "finalize_decision",
                    "dependencies": ["1", "2"],
                    "expected_outcome": "Final screening decision"
                }
            ],
            "estimated_iterations": 3,
            "strategy": "adaptive",
            "risk_factors": []
        }
    
    def adapt_plan(
        self,
        current_plan: Dict[str, Any],
        observations: List[Dict[str, Any]],
        current_step: str
    ) -> Dict[str, Any]:
        """
        Adapt the plan based on new observations.
        """
        logger.info(f"Adapting plan based on {len(observations)} observations")
        
        # Simple adaptation: mark completed steps, add new steps if needed
        completed_steps = [obs.get("step_id") for obs in observations if obs.get("status") == "completed"]
        
        # Update plan
        for step in current_plan.get("steps", []):
            if step["step_id"] in completed_steps:
                step["status"] = "completed"
            elif step["step_id"] == current_step:
                step["status"] = "in_progress"
        
        return current_plan
    
    def get_next_step(
        self,
        plan: Dict[str, Any],
        completed_steps: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the next step that can be executed (all dependencies met).
        """
        steps = plan.get("steps", [])
        
        for step in steps:
            step_id = step.get("step_id")
            if step_id in completed_steps:
                continue
            
            # Check if dependencies are met
            dependencies = step.get("dependencies", [])
            if all(dep in completed_steps for dep in dependencies):
                return step
        
        return None
    
    def is_plan_complete(self, plan: Dict[str, Any], completed_steps: List[str]) -> bool:
        """Check if all steps in the plan are completed."""
        steps = plan.get("steps", [])
        step_ids = [s.get("step_id") for s in steps]
        return all(step_id in completed_steps for step_id in step_ids)

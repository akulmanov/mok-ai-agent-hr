"""
Agent Reasoner - ReAct pattern implementation for autonomous reasoning.
"""
import logging
import json
import re
from typing import Dict, List, Any, Optional
from app.llm_service import LLMService

logger = logging.getLogger(__name__)


class AgentReasoner:
    """
    Implements ReAct (Reasoning + Acting) pattern for autonomous agent reasoning.
    The agent reasons about what to do, acts, observes results, and iterates.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    def reason_next_action(
        self,
        goal: str,
        context: Dict[str, Any],
        available_tools: str,
        memory_summary: Dict[str, Any],
        recent_observations: List[Dict],
        recent_actions: List[Dict]
    ) -> Dict[str, Any]:
        """
        Reason about what action to take next using ReAct pattern.
        
        Returns:
            {
                "thought": str,  # Reasoning process
                "action": str,    # Tool name to use
                "action_input": Dict,  # Parameters for the tool
                "confidence": float,  # Confidence in this action
                "reasoning": str  # Why this action
            }
        """
        logger.info("Reasoning about next action...")
        
        system_prompt = """Вы - автономный AI агент, использующий паттерн ReAct (Reasoning + Acting).

Ваш процесс:
1. THOUGHT: Проанализируйте текущую ситуацию, цель, контекст и память
2. ACTION: Выберите инструмент и параметры для выполнения действия
3. OBSERVATION: (будет добавлено после выполнения действия)
4. Повторяйте до достижения цели

ПРАВИЛА:
- Всегда начинайте с THOUGHT
- Используйте доступные инструменты для достижения цели
- Если информации недостаточно, используйте инструменты для её получения
- Если есть неопределенности, используйте инструменты для их разрешения
- Будьте конкретны в выборе инструментов и параметров
- Оцените свою уверенность (0.0-1.0)

Верните JSON объект с:
- thought: Ваши размышления о текущей ситуации
- action: Имя инструмента для использования
- action_input: Параметры для инструмента (словарь)
- confidence: Уверенность в этом действии (0.0-1.0)
- reasoning: Почему вы выбрали это действие"""
        
        # Format observations
        obs_text = "\n".join([
            f"- {obs.get('type', 'unknown')}: {obs.get('summary', str(obs))}"
            for obs in recent_observations[-5:]
        ]) if recent_observations else "Нет наблюдений"
        
        # Format actions
        actions_text = "\n".join([
            f"- {act.get('action', {}).get('type', 'unknown')}: {act.get('result', {}).get('summary', 'executed')}"
            for act in recent_actions[-5:]
        ]) if recent_actions else "Нет выполненных действий"
        
        memory_str = json.dumps(memory_summary, indent=2, ensure_ascii=False)
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        
        user_prompt = f"""ЦЕЛЬ: {goal}

КОНТЕКСТ:
{context_str}

ПАМЯТЬ:
{memory_str}

ПОСЛЕДНИЕ НАБЛЮДЕНИЯ:
{obs_text}

ПОСЛЕДНИЕ ДЕЙСТВИЯ:
{actions_text}

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{available_tools}

Проанализируйте ситуацию и решите, какое действие предпринять дальше.
Верните только валидный JSON."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm._call_llm(messages, response_format={"type": "json_object"})
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            
            # Validate structure
            if "action" not in result:
                logger.warning("LLM response missing 'action', using default")
                result["action"] = "evaluate"
            
            if "action_input" not in result:
                result["action_input"] = {}
            
            if "confidence" not in result:
                result["confidence"] = 0.5
            
            if "thought" not in result:
                result["thought"] = "No reasoning provided"
            
            if "reasoning" not in result:
                result["reasoning"] = result.get("thought", "No reasoning provided")
            
            logger.info(f"Reasoned action: {result['action']} (confidence: {result.get('confidence', 0.0):.2f})")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reasoning response: {e}")
            # Return a safe default action
            return {
                "thought": "Failed to parse reasoning, using default action",
                "action": "evaluate",
                "action_input": {},
                "confidence": 0.3,
                "reasoning": "Fallback to basic evaluation"
            }
    
    def reflect_on_result(
        self,
        action: Dict[str, Any],
        result: Dict[str, Any],
        goal: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reflect on the result of an action and determine next steps.
        
        Returns:
            {
                "success": bool,
                "observations": List[str],
                "uncertainties": List[str],
                "confidence_delta": float,
                "next_steps": List[str],
                "should_continue": bool
            }
        """
        logger.info("Reflecting on action result...")
        
        system_prompt = """Вы анализируете результат выполненного действия и определяете следующие шаги.

Оцените:
1. Успешность действия
2. Что было узнано (наблюдения)
3. Какие неопределенности остались
4. Как изменилась уверенность
5. Что делать дальше
6. Следует ли продолжать

Верните JSON объект с:
- success: bool - было ли действие успешным
- observations: List[str] - что было узнано
- uncertainties: List[str] - какие неопределенности остались
- confidence_delta: float - изменение уверенности (-1.0 до 1.0)
- next_steps: List[str] - предложения для следующих шагов
- should_continue: bool - следует ли продолжать работу"""
        
        action_str = json.dumps(action, indent=2, ensure_ascii=False)
        result_str = json.dumps(result, indent=2, ensure_ascii=False)
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        
        user_prompt = f"""ЦЕЛЬ: {goal}

ВЫПОЛНЕННОЕ ДЕЙСТВИЕ:
{action_str}

РЕЗУЛЬТАТ:
{result_str}

КОНТЕКСТ:
{context_str}

Проанализируйте результат и определите следующие шаги.
Верните только валидный JSON."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm._call_llm(messages, response_format={"type": "json_object"})
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            reflection = json.loads(response)
            
            # Validate structure
            if "success" not in reflection:
                reflection["success"] = True
            if "observations" not in reflection:
                reflection["observations"] = []
            if "uncertainties" not in reflection:
                reflection["uncertainties"] = []
            if "confidence_delta" not in reflection:
                reflection["confidence_delta"] = 0.0
            if "next_steps" not in reflection:
                reflection["next_steps"] = []
            if "should_continue" not in reflection:
                reflection["should_continue"] = True
            
            logger.info(f"Reflection: success={reflection['success']}, should_continue={reflection['should_continue']}")
            return reflection
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reflection: {e}")
            return {
                "success": True,
                "observations": ["Action completed"],
                "uncertainties": [],
                "confidence_delta": 0.0,
                "next_steps": ["Continue evaluation"],
                "should_continue": True
            }
    
    def should_stop(
        self,
        goal: str,
        confidence: float,
        uncertainties: List[str],
        iterations: int,
        max_iterations: int
    ) -> Dict[str, Any]:
        """
        Determine if the agent should stop working.
        
        Returns:
            {
                "should_stop": bool,
                "reason": str,
                "confidence": float
            }
        """
        # Hard stop conditions
        if iterations >= max_iterations:
            return {
                "should_stop": True,
                "reason": f"Reached maximum iterations ({max_iterations})",
                "confidence": confidence
            }
        
        # High confidence and no uncertainties
        if confidence >= 0.85 and len(uncertainties) == 0:
            return {
                "should_stop": True,
                "reason": "High confidence achieved with no uncertainties",
                "confidence": confidence
            }
        
        # Very low confidence after multiple iterations
        if iterations >= 3 and confidence < 0.3:
            return {
                "should_stop": True,
                "reason": "Low confidence persists after multiple iterations",
                "confidence": confidence
            }
        
        return {
            "should_stop": False,
            "reason": "Continue working",
            "confidence": confidence
        }

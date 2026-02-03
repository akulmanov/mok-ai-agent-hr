"""
Agent Memory System - Manages context, working memory, and long-term patterns.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Sophisticated memory system for the agent.
    Manages short-term working memory, long-term patterns, and context.
    """
    
    def __init__(self, max_short_term_size: int = 50, max_long_term_size: int = 1000):
        self.max_short_term_size = max_short_term_size
        self.max_long_term_size = max_long_term_size
        
        # Short-term working memory (current session)
        self.short_term = {
            "observations": deque(maxlen=max_short_term_size),
            "actions": deque(maxlen=max_short_term_size),
            "decisions": deque(maxlen=max_short_term_size),
            "uncertainties": [],
            "confidence_history": [],
            "current_goal": None,
            "sub_goals": [],
            "completed_goals": [],
            "context": {}
        }
        
        # Long-term memory (patterns, learnings)
        self.long_term = {
            "successful_strategies": [],
            "failed_attempts": [],
            "patterns": {},
            "preferences": {}
        }
        
        # Episodic memory (specific events)
        self.episodic = []
        
    def add_observation(self, observation: Dict[str, Any]):
        """Add an observation to working memory."""
        observation["timestamp"] = datetime.now().isoformat()
        self.short_term["observations"].append(observation)
        logger.debug(f"Added observation: {observation.get('type', 'unknown')}")
    
    def add_action(self, action: Dict[str, Any], result: Optional[Dict[str, Any]] = None):
        """Record an action and its result."""
        action_record = {
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.short_term["actions"].append(action_record)
        logger.debug(f"Recorded action: {action.get('type', 'unknown')}")
    
    def add_uncertainty(self, uncertainty: str, context: Optional[Dict] = None):
        """Track uncertainties that need resolution."""
        uncertainty_record = {
            "text": uncertainty,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }
        self.short_term["uncertainties"].append(uncertainty_record)
        logger.debug(f"Added uncertainty: {uncertainty}")
    
    def resolve_uncertainty(self, uncertainty_text: str):
        """Mark an uncertainty as resolved."""
        for unc in self.short_term["uncertainties"]:
            if unc["text"] == uncertainty_text and not unc["resolved"]:
                unc["resolved"] = True
                unc["resolved_at"] = datetime.now().isoformat()
                logger.debug(f"Resolved uncertainty: {uncertainty_text}")
                return True
        return False
    
    def update_confidence(self, confidence: float, reason: Optional[str] = None):
        """Track confidence scores over time."""
        confidence_record = {
            "value": confidence,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.short_term["confidence_history"].append(confidence_record)
        logger.debug(f"Updated confidence: {confidence:.2f} - {reason}")
    
    def get_current_confidence(self) -> float:
        """Get the most recent confidence score."""
        if self.short_term["confidence_history"]:
            return self.short_term["confidence_history"][-1]["value"]
        return 0.0
    
    def set_goal(self, goal: str, sub_goals: Optional[List[str]] = None):
        """Set the current goal and sub-goals."""
        self.short_term["current_goal"] = goal
        self.short_term["sub_goals"] = sub_goals or []
        logger.info(f"Set goal: {goal}")
    
    def complete_sub_goal(self, sub_goal: str):
        """Mark a sub-goal as completed."""
        if sub_goal in self.short_term["sub_goals"]:
            self.short_term["sub_goals"].remove(sub_goal)
            self.short_term["completed_goals"].append(sub_goal)
            logger.debug(f"Completed sub-goal: {sub_goal}")
    
    def update_context(self, key: str, value: Any):
        """Update context information."""
        self.short_term["context"][key] = value
        logger.debug(f"Updated context: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context information."""
        return self.short_term["context"].get(key, default)
    
    def get_recent_observations(self, n: int = 5) -> List[Dict]:
        """Get the most recent N observations."""
        return list(self.short_term["observations"])[-n:]
    
    def get_recent_actions(self, n: int = 5) -> List[Dict]:
        """Get the most recent N actions."""
        return list(self.short_term["actions"])[-n:]
    
    def get_unresolved_uncertainties(self) -> List[Dict]:
        """Get all unresolved uncertainties."""
        return [u for u in self.short_term["uncertainties"] if not u["resolved"]]
    
    def learn_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]):
        """Store a learned pattern in long-term memory."""
        if pattern_name not in self.long_term["patterns"]:
            self.long_term["patterns"][pattern_name] = []
        self.long_term["patterns"][pattern_name].append(pattern_data)
        logger.debug(f"Learned pattern: {pattern_name}")
    
    def get_pattern(self, pattern_name: str) -> List[Dict]:
        """Retrieve learned patterns."""
        return self.long_term["patterns"].get(pattern_name, [])
    
    def record_success(self, strategy: str, context: Dict[str, Any]):
        """Record a successful strategy."""
        success_record = {
            "strategy": strategy,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.long_term["successful_strategies"].append(success_record)
        logger.debug(f"Recorded successful strategy: {strategy}")
    
    def record_failure(self, strategy: str, context: Dict[str, Any], reason: str):
        """Record a failed strategy."""
        failure_record = {
            "strategy": strategy,
            "context": context,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.long_term["failed_attempts"].append(failure_record)
        logger.debug(f"Recorded failed strategy: {strategy}")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of current memory state."""
        return {
            "current_goal": self.short_term["current_goal"],
            "sub_goals": self.short_term["sub_goals"],
            "completed_goals": self.short_term["completed_goals"],
            "confidence": self.get_current_confidence(),
            "unresolved_uncertainties": len(self.get_unresolved_uncertainties()),
            "recent_observations": len(self.short_term["observations"]),
            "recent_actions": len(self.short_term["actions"]),
            "context_keys": list(self.short_term["context"].keys())
        }
    
    def clear_short_term(self):
        """Clear short-term memory (useful for new sessions)."""
        self.short_term = {
            "observations": deque(maxlen=self.max_short_term_size),
            "actions": deque(maxlen=self.max_short_term_size),
            "decisions": deque(maxlen=self.max_short_term_size),
            "uncertainties": [],
            "confidence_history": [],
            "current_goal": None,
            "sub_goals": [],
            "completed_goals": [],
            "context": {}
        }
        logger.info("Cleared short-term memory")

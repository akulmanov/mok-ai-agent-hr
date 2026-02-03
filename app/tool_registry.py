"""
Tool Registry - Dynamic tool selection and execution system.
"""
import logging
from typing import Dict, List, Any, Optional, Callable
from inspect import signature

logger = logging.getLogger(__name__)


class Tool:
    """Represents a tool that the agent can use."""
    
    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any],
        category: str = "general"
    ):
        self.name = name
        self.func = func
        self.description = description
        self.parameters = parameters
        self.category = category
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        try:
            # Validate parameters
            sig = signature(self.func)
            valid_kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name in kwargs:
                    valid_kwargs[param_name] = kwargs[param_name]
            
            result = self.func(**valid_kwargs)
            logger.debug(f"Tool {self.name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category
        }


class ToolRegistry:
    """
    Registry of all available tools for the agent.
    Manages tool registration, selection, and execution.
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.tool_categories: Dict[str, List[str]] = {}
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any],
        category: str = "general"
    ):
        """Register a new tool."""
        tool = Tool(name, func, description, parameters, category)
        self.tools[name] = tool
        
        if category not in self.tool_categories:
            self.tool_categories[category] = []
        self.tool_categories[category].append(name)
        
        logger.info(f"Registered tool: {name} (category: {category})")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tools, optionally filtered by category."""
        if category:
            tool_names = self.tool_categories.get(category, [])
            return [self.tools[name].to_dict() for name in tool_names if name in self.tools]
        return [tool.to_dict() for tool in self.tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        return tool.execute(**kwargs)
    
    def get_tools_for_reasoning(self) -> str:
        """Get a formatted string of all tools for LLM reasoning."""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append(
                f"- {tool.name} ({tool.category}): {tool.description}\n"
                f"  Parameters: {tool.parameters}"
            )
        return "\n".join(tools_list)
    
    def suggest_tools(
        self,
        goal: str,
        context: Dict[str, Any],
        llm_service
    ) -> List[str]:
        """
        Use LLM to suggest which tools might be useful for a goal.
        """
        import json
        
        system_prompt = """Вы помогаете агенту выбрать подходящие инструменты для достижения цели.
Проанализируйте цель и контекст, и предложите список инструментов, которые могут быть полезны.
Верните JSON массив строк с именами инструментов."""
        
        available_tools = self.get_tools_for_reasoning()
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        
        user_prompt = f"""ЦЕЛЬ: {goal}

КОНТЕКСТ:
{context_str}

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{available_tools}

Верните JSON массив строк с именами наиболее подходящих инструментов."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = llm_service._call_llm(messages, response_format={"type": "json_object"})
            result = json.loads(response)
            
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "tools" in result:
                return result["tools"]
            return []
        except Exception as e:
            logger.error(f"Error suggesting tools: {e}")
            return []

from langchain_core.tools import BaseTool, StructuredTool, tool
from typing import List, Optional


@tool
def search_tool(query: str) -> str:
    """Search for information based on a query."""
    return f"Search results for: {query}"


@tool
def calculator_tool(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        allowed_chars = set('0123456789+-*/()., ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


class ToolRegistry:
    def __init__(self):
        self.tools: List[BaseTool] = []
    
    def register(self, tool: BaseTool):
        self.tools.append(tool)
        return tool
    
    def register_function(self, func, name: Optional[str] = None, description: Optional[str] = None):
        tool_instance = StructuredTool.from_function(
            func=func,
            name=name or func.__name__,
            description=description or func.__doc__
        )
        self.register(tool_instance)
        return tool_instance
    
    def get_tools(self) -> List[BaseTool]:
        return self.tools
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None


tool_registry = ToolRegistry()
tool_registry.register(search_tool)
tool_registry.register(calculator_tool)

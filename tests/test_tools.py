import pytest
from core.tools import calculator_tool, search_tool, tool_registry

def test_calculator_tool():
    """Test calculator tool with valid expression."""
    result = calculator_tool.invoke({"expression": "2+2"})
    assert result == "4"

def test_calculator_tool_invalid():
    """Test calculator tool with invalid expression."""
    result = calculator_tool.invoke({"expression": "import os"})
    assert "Error" in result

def test_search_tool():
    """Test search tool."""
    result = search_tool.invoke({"query": "test query"})
    assert "test query" in result

def test_tool_registry():
    """Test tool registry."""
    tools = tool_registry.get_tools()
    assert len(tools) >= 2
    
    calc = tool_registry.get_tool_by_name("calculator_tool")
    assert calc is not None

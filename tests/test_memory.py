import pytest
from core.memory import memory_manager
from langchain_core.messages import HumanMessage, AIMessage

def test_memory_manager():
    """Test memory manager basic operations."""
    session_id = "test_session"
    
    memory_manager.add_message(session_id, HumanMessage(content="Hello"))
    memory_manager.add_message(session_id, AIMessage(content="Hi there"))
    
    messages = memory_manager.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[1].content == "Hi there"
    
    memory_manager.clear_session(session_id)
    messages = memory_manager.get_messages(session_id)
    assert len(messages) == 0

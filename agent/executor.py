from langchain_core.messages import HumanMessage
from agent.graph import agent_graph
from agent.state import AgentState
from typing import Dict, Any, AsyncGenerator


class AgentExecutor:
    def __init__(self):
        self.graph = agent_graph
    
    async def execute(self, user_input: str, session_id: str = "default") -> Dict[str, Any]:
        """Execute the agent with user input."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_input)],
            "context": "",
            "next_action": ""
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        return {
            "response": result["messages"][-1].content if result["messages"] else "",
            "context": result.get("context", ""),
            "session_id": session_id
        }
    
    async def execute_stream(self, user_input: str, session_id: str = "default") -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the agent with streaming output."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_input)],
            "context": "",
            "next_action": ""
        }
        
        result = await self.graph.ainvoke(initial_state)
        response = result["messages"][-1].content if result["messages"] else ""
        total_length = len(response)
        
        for i, char in enumerate(response):
            yield {
                "chunk": char,
                "done": i == len(response) - 1,
                "progress": (i + 1) / total_length,
                "session_id": session_id
            }
    
    def execute_sync(self, user_input: str, session_id: str = "default") -> Dict[str, Any]:
        """Synchronous execution of the agent."""
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_input)],
            "context": "",
            "next_action": ""
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "response": result["messages"][-1].content if result["messages"] else "",
            "context": result.get("context", ""),
            "session_id": session_id
        }


agent_executor = AgentExecutor()

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import retrieval_node, agent_node, tool_node


def create_agent_graph():
    """Create the agent workflow graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Add edges
    workflow.set_entry_point("retrieval")
    workflow.add_edge("retrieval", "agent")
    
    # Conditional routing
    def should_continue(state: AgentState) -> str:
        next_action = state.get("next_action", "end")
        if next_action == "tools":
            return "tools"
        return "end"
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


agent_graph = create_agent_graph()

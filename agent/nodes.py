from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.state import AgentState
from agent.prompts import get_system_prompt
from core import ModelManager, rag_manager, tool_registry


def retrieval_node(state: AgentState) -> AgentState:
    """Retrieve relevant context from RAG."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    docs = rag_manager.similarity_search(last_message, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    return {"context": context}


def agent_node(state: AgentState) -> AgentState:
    """Main agent reasoning node."""
    llm = ModelManager.get_llm()
    messages = state["messages"]
    context = state.get("context", "")
    
    system_prompt = get_system_prompt(context=context)
    full_messages = [SystemMessage(content=system_prompt)] + list(messages)
    
    response = llm.invoke(full_messages)
    
    return {"messages": [response], "next_action": "end"}


def tool_node(state: AgentState) -> AgentState:
    """Execute tools based on agent decision."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Tool execution logic here
    result = "Tool execution result"
    
    return {"messages": [AIMessage(content=result)]}

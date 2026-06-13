from langgraph.graph import StateGraph, START, END
from src.schema import AgentState
from src.agents.comms import comms_agent_node
from src.router import orchestrator_router
from src.security import pii_scrubber_node
from src.memory.checkpointer import get_checkpointer

def create_orchestrator_graph():
    """
    Builds the LangGraph state machine for the Orchestrator.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("pii_scrubber", pii_scrubber_node)
    workflow.add_node("orchestrator", orchestrator_router)
    
    workflow.add_node("comms_agent", comms_agent_node)
    
    # Graph execution flow
    workflow.add_edge(START, "pii_scrubber")
    workflow.add_edge("pii_scrubber", "orchestrator")
    
    # Conditional edges from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        lambda state: state.get("next_node", "finish"),
        {
            "comms_agent": "comms_agent",
            "finish": END
        }
    )
    
    # Edges from agents back to END 
    workflow.add_edge("comms_agent", END)
    
    # Attach the Checkpointer for state persistence
    checkpointer = get_checkpointer()
    
    return workflow.compile(checkpointer=checkpointer)

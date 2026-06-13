from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from src.schema import AgentState

def healthcare_internal_logic(state: AgentState):
    """
    Internal reasoning node for the Healthcare Agent Sub-graph.
    HIPAA-aware workflows.
    """
    llm = state.get("assigned_llm", "claude-3-5-sonnet")
    response_msg = AIMessage(content=f"[Healthcare Agent] Executing HIPAA-aware workflows using {llm}. Tools: EHR.")
    return {"messages": [response_msg], "final_response": response_msg.content}

def get_healthcare_subgraph():
    workflow = StateGraph(AgentState)
    workflow.add_node("healthcare_logic", healthcare_internal_logic)
    workflow.add_edge(START, "healthcare_logic")
    workflow.add_edge("healthcare_logic", END)
    return workflow.compile()

def healthcare_agent_node(state: AgentState):
    return get_healthcare_subgraph().invoke(state)

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from src.schema import AgentState

def finance_internal_logic(state: AgentState):
    """
    Internal reasoning node for the Finance Agent Sub-graph.
    """
    llm = state.get("assigned_llm", "claude-3-5-sonnet")
    response_msg = AIMessage(content=f"[Finance Agent] Processing financial workflows using {llm}. Tools: ERP/Billing.")
    return {"messages": [response_msg], "final_response": response_msg.content}

def get_finance_subgraph():
    workflow = StateGraph(AgentState)
    workflow.add_node("finance_logic", finance_internal_logic)
    workflow.add_edge(START, "finance_logic")
    workflow.add_edge("finance_logic", END)
    return workflow.compile()

def finance_agent_node(state: AgentState):
    return get_finance_subgraph().invoke(state)

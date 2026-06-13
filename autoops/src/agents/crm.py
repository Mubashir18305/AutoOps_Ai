from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from src.schema import AgentState

def crm_internal_logic(state: AgentState):
    """
    Internal reasoning node for the CRM Agent Sub-graph.
    """
    llm = state.get("assigned_llm", "gpt-4o")
    response_msg = AIMessage(content=f"[CRM Agent] Managing customer data using {llm}. Tools: Salesforce/Notion.")
    return {"messages": [response_msg], "final_response": response_msg.content}

def get_crm_subgraph():
    workflow = StateGraph(AgentState)
    workflow.add_node("crm_logic", crm_internal_logic)
    workflow.add_edge(START, "crm_logic")
    workflow.add_edge("crm_logic", END)
    return workflow.compile()

def crm_agent_node(state: AgentState):
    return get_crm_subgraph().invoke(state)

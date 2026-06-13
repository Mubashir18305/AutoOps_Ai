from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from src.schema import AgentState

def devops_internal_logic(state: AgentState):
    """
    Internal reasoning node for the DevOps Agent Sub-graph.
    """
    llm = state.get("assigned_llm", "gpt-4o")
    response_msg = AIMessage(content=f"[DevOps Agent] Executing CI/CD pipelines using {llm}. Tools: GitHub/APIs.")
    return {"messages": [response_msg], "final_response": response_msg.content}

def get_devops_subgraph():
    workflow = StateGraph(AgentState)
    workflow.add_node("devops_logic", devops_internal_logic)
    workflow.add_edge(START, "devops_logic")
    workflow.add_edge("devops_logic", END)
    return workflow.compile()

def devops_agent_node(state: AgentState):
    return get_devops_subgraph().invoke(state)

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from src.schema import AgentState

def research_internal_logic(state: AgentState):
    """
    Internal reasoning node for the Research Agent Sub-graph.
    """
    llm = state.get("assigned_llm", "gpt-4o")
    response_msg = AIMessage(content=f"[Research Agent] Scraping and synthesizing data using {llm}. Tools: Web Scraper.")
    return {"messages": [response_msg], "final_response": response_msg.content}

def get_research_subgraph():
    workflow = StateGraph(AgentState)
    workflow.add_node("research_logic", research_internal_logic)
    workflow.add_edge(START, "research_logic")
    workflow.add_edge("research_logic", END)
    return workflow.compile()

def research_agent_node(state: AgentState):
    return get_research_subgraph().invoke(state)

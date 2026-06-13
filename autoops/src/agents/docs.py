from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from src.schema import AgentState
from src.utils import get_llm
from src.memory.vector_db import VectorDBManager

@tool
async def search_knowledge_base(query: str) -> str:
    """
    Search the organizational Vector Database for documents, policies, and contracts.
    """
    vector_db = VectorDBManager()
    docs = await vector_db.query_documents(query=query, top_k=3)
    
    if not docs:
        return "No relevant documents found."
        
    doc_context = "\n".join([f"- {d.page_content} (Source: {d.metadata.get('source')})" for d in docs])
    return f"Found the following documents:\n{doc_context}"

async def docs_agent_node(state: AgentState):
    """
    Docs Agent: Uses ReAct agent to search VectorDB and synthesize documents.
    """
    llm_name = state.get("assigned_llm", "sarvam-105b")
    
    try:
        llm = get_llm(llm_name)
        tools = [search_knowledge_base]
        
        agent = create_react_agent(llm, tools=tools)
        
        # Pass the existing conversation to the agent
        result = await agent.ainvoke({"messages": state.get("messages", [])})
        
        existing_count = len(state.get("messages", []))
        new_messages = result["messages"][existing_count:]
        final_response = new_messages[-1].content if new_messages else ""
        
        return {"messages": new_messages, "final_response": final_response}
        
    except Exception as e:
        error_msg = AIMessage(content=f"[Docs Agent Error] Failed to execute LLM: {e}")
        return {"messages": [error_msg], "final_response": error_msg.content}

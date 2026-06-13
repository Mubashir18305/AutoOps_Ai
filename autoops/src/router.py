import os
from src.schema import AgentState
from pydantic import BaseModel, Field
from src.utils import get_llm
from langchain_core.messages import SystemMessage

class RouteDecision(BaseModel):
    next_node: str = Field(description="The next agent to route to: 'comms_agent' or 'finish'.")
    assigned_llm: str = Field(description="The LLM to use. Must be 'sarvam-105b'.")

def orchestrator_router(state: AgentState) -> dict:
    """
    Analyzes the current state, decides the target Specialist Agent, 
    and assigns the Sarvam LLM.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"next_node": "finish", "assigned_llm": "sarvam-105b"}
        
    # Instantiate the Sarvam LLM via our factory
    llm = get_llm("sarvam-105b")
    structured_llm = llm.with_structured_output(RouteDecision)
    
    system_prompt = SystemMessage(content="""You are the Orchestrator Router for an Enterprise AI OS.
Analyze the user's latest request and route it to the appropriate agent:
- comms_agent: Email, WhatsApp, Slack, Teams

We exclusively use the Sarvam API for processing. Set assigned_llm to 'sarvam-105b'.
Only output the requested JSON format without any additional reasoning.
""")
    
    # Only pass the last 3 messages to avoid context confusion and token overflow
    router_messages = [system_prompt] + messages[-3:]
    
    try:
        decision = structured_llm.invoke(router_messages)
        return {"next_node": decision.next_node, "assigned_llm": decision.assigned_llm}
    except Exception as e:
        print(f"Router LLM failed: {e}")
        # Basic keyword fallback in case the Sarvam API key isn't set yet
        last_msg = messages[-1].content.lower()
        if "contract" in last_msg or "document" in last_msg:
            return {"next_node": "docs_agent", "assigned_llm": "sarvam-105b"}
        return {"next_node": "comms_agent", "assigned_llm": "sarvam-105b"}

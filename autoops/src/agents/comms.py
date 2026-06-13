from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from src.schema import AgentState
from src.utils import get_llm
from langchain_core.tools import tool
import datetime
import re

async def comms_agent_node(state: AgentState):
    """
    Comms Agent Sub-graph: Uses robust closures to bypass Sarvam LLM's inability to generate JSON tool arguments.
    """
    llm_name = state.get("assigned_llm", "sarvam-105b")
    llm = get_llm(llm_name)
    user_msg = state.get("messages", [])[-1].content if state.get("messages") else ""
    
    now = datetime.datetime.now()
    current_date = now.strftime("%Y/%m/%d")
    yesterday_date = (now - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
    current_time = now.strftime("%I:%M %p")
    
    # --- ROBUST CLOSURE TOOLS ---
    # Since Sarvam-105b always passes {} for tool arguments, we extract arguments via direct text prompts
    from src.mcp_server.comms_server import get_gmail_service
    
    @tool
    def count_emails() -> str:
        """Count emails. Use this whenever the user asks to count or tally emails."""
        # Deterministic override for common requests to avoid LLM hallucinations and PST timezone quirks
        user_lower = user_msg.lower()
        if "yesterday" in user_lower:
            query = f"after:{yesterday_date} before:{current_date}"
            if "unread" in user_lower:
                query += " is:unread"
        elif "today" in user_lower:
            query = f"after:{current_date}"
            if "unread" in user_lower:
                query += " is:unread"
        else:
            prompt = f"Convert the timeframe/request into a Gmail search query (e.g., 'after:{yesterday_date}', 'is:unread', 'from:boss'). Today is {current_date}. Request: '{user_msg}'. Output ONLY the raw Gmail query string, nothing else."
            query = llm.invoke(prompt).content.strip().replace('"', '').replace("'", "")
            if not query or "query" in query.lower():
                query = "is:unread"
        
        try:
            service = get_gmail_service()
            results = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
            messages = results.get("messages", [])
            count = len(messages)
            if count == 500:
                return f"Count of emails matching '{query}': 500+ (limit reached)"
            return f"Exact count of emails matching '{query}': {count}"
        except Exception as e:
            return f"Failed to count: {e}"

    @tool
    def list_emails() -> str:
        """Search and list emails. Use this whenever the user asks to see, list, or check their inbox."""
        user_lower = user_msg.lower()
        if "yesterday" in user_lower:
            query = f"after:{yesterday_date} before:{current_date}"
            if "unread" in user_lower:
                query += " is:unread"
        elif "today" in user_lower:
            query = f"after:{current_date}"
            if "unread" in user_lower:
                query += " is:unread"
        else:
            prompt = f"Convert the timeframe/request into a Gmail search query. Today is {current_date}. Request: '{user_msg}'. Output ONLY the raw Gmail query string."
            query = llm.invoke(prompt).content.strip().replace('"', '').replace("'", "")
            if not query or "query" in query.lower():
                query = "is:unread"
            
        try:
            service = get_gmail_service()
            results = service.users().messages().list(userId="me", q=query, maxResults=15).execute()
            messages = results.get("messages", [])
            if not messages:
                return f"No emails found matching query: {query}"
                
            email_summaries = []
            for msg in messages:
                msg_id = msg["id"]
                msg_details = service.users().messages().get(userId="me", id=msg_id, format="metadata", metadataHeaders=["Subject", "From", "Date"]).execute()
                headers = msg_details.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
                sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
                date_time = next((h["value"] for h in headers if h["name"].lower() == "date"), "Unknown Date")
                email_summaries.append(f"ID: {msg_id}\nFrom: {sender}\nSubject: {subject}\nDate: {date_time}\n---")
            
            total_estimate = results.get("resultSizeEstimate", len(messages))
            return f"Query used: '{query}'. Estimated total: {total_estimate}\nShowing top {len(messages)}:\n\n" + "\n".join(email_summaries)
        except Exception as e:
            return f"Failed to list: {e}"

    @tool
    def read_email_details() -> str:
        """Read the full content of a specific email. Use this when the user asks to read or summarize a specific email ID."""
        prompt = f"Extract the specific email ID the user wants to read from this request: '{user_msg}'. Output ONLY the exact ID string, nothing else."
        email_id = llm.invoke(prompt).content.strip().replace('"', '').replace("'", "")
        
        try:
            service = get_gmail_service()
            message = service.users().messages().get(userId="me", id=email_id, format="full").execute()
            snippet = message.get("snippet", "")
            return f"Email Snippet/Content for ID {email_id}:\n{snippet}\n(Tell the user the summary)"
        except Exception as e:
            return f"Failed to read email {email_id}: {e}"

    tools = [count_emails, list_emails, read_email_details]
    print(f"DEBUG: Loaded robust closure tools")
    
    system_prompt = (
        f"You are the Communications Specialist Agent. The current date/time is {current_date} at {current_time}.\n"
        "You have powerful tools that automatically infer parameters from the user's message.\n"
        "- To count emails, call `count_emails`.\n"
        "- To list emails, call `list_emails`.\n"
        "- To read an email, call `read_email_details`.\n"
        "You do NOT need to pass any arguments. Just call the tool.\n"
        "Present lists in a clean, numbered list with emojis:\n"
        "1. 📧 *From:* Sender Name | *Subject:* Email Subject | *Date:* Date/Time\n"
    )
    
    try:
        agent = create_react_agent(llm, tools=tools, prompt=system_prompt)
        result = await agent.ainvoke({"messages": state.get("messages", [])})
        
        print("\n--- DEBUG: Agent Messages ---")
        for i, m in enumerate(result["messages"]):
            print(f"[{i}] {type(m).__name__}: {str(m.content)[:200]}")
        print("-----------------------------\n")
        
        existing_count = len(state.get("messages", []))
        new_messages = result["messages"][existing_count:]
        
        final_response = new_messages[-1].content if new_messages else "Comms executed."
        if not str(final_response).strip():
            tool_output = ""
            for m in reversed(new_messages):
                if type(m).__name__ == 'ToolMessage':
                    tool_output = str(m.content)
                    break
            if tool_output:
                final_response = f"I processed the data! Here is the raw output:\n\n{tool_output}"
            else:
                final_response = "I encountered an internal error: empty response."
                
        return {"messages": new_messages, "final_response": final_response}
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = AIMessage(content=f"[Comms Agent Error] Failed to execute LLM: {e}\nTraceback:\n{tb}")
        return {"messages": [error_msg], "final_response": error_msg.content}

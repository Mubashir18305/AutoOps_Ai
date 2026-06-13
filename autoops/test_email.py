import asyncio
from src.orchestrator import create_orchestrator_graph
from langchain_core.messages import HumanMessage
import uuid
from dotenv import load_dotenv
load_dotenv()
import os

os.environ["PYTHONUTF8"] = "1"

async def test():
    app = create_orchestrator_graph()
    thread_id = str(uuid.uuid4())
    initial_state = {
        "messages": [HumanMessage(content="Hey, can you check my recent emails and summarize the most important ones for me?")],
        "context": {"user_id": "+1234567890", "source": "whatsapp"},
        "next_node": "",
        "final_response": ""
    }
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = await app.ainvoke(initial_state, config=config)
        print("FINAL RESPONSE:", result.get("final_response"))
    except Exception as e:
        import traceback
        print("CRASHED:", traceback.format_exc())

asyncio.run(test())

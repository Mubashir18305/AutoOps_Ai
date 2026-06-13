import asyncio
from dotenv import load_dotenv
load_dotenv()
from src.orchestrator import create_orchestrator_graph
from langchain_core.messages import HumanMessage

async def main():
    graph = create_orchestrator_graph()
    
    # Payload for WhatsApp
    state = {
        "messages": [HumanMessage(content="Can you send a WhatsApp message to +1234567890 saying 'Hello from Sarvam AI OS!' ?")],
        "context": {"user_id": "whatsapp_test"},
    }
    print("Sending WhatsApp request to Orchestrator...")
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "test_whatsapp"}})
    print("\n--- FINAL OUTPUT ---")
    print(result.get('final_response'))

if __name__ == "__main__":
    asyncio.run(main())

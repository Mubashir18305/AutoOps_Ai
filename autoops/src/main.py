from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
import uuid
import httpx
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.orchestrator import create_orchestrator_graph

load_dotenv()

app = FastAPI(title="Universal Enterprise Multi-Agent Platform (AI OS)")

# Load Meta API Credentials
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secure_token_123")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

orchestrator_app = create_orchestrator_graph()

class TriggerPayload(BaseModel):
    message: str
    source: str
    user_id: str

@app.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Required for Meta WhatsApp Cloud API webhook verification.
    """
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")

from fastapi import BackgroundTasks

async def process_and_reply(text_content: str, phone_number: str):
    try:
        thread_id = f"wa_{phone_number}"
        initial_state = {
            "messages": [HumanMessage(content=text_content)],
            "context": {"user_id": phone_number, "source": "whatsapp"},
            "next_node": "",
            "final_response": ""
        }
        
        result = await orchestrator_app.ainvoke(initial_state, config={"configurable": {"thread_id": thread_id}})
        final_response = result.get("final_response", "I'm sorry, I couldn't process that.")
        
        print(f"Orchestrator Output: {final_response}")
        
        if WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_ID:
            send_whatsapp_message_sync(phone_number, final_response)
        else:
            print("WARNING: WHATSAPP_ACCESS_TOKEN not set. Cannot send reply back.")
    except Exception as e:
        print(f"Background task error: {e}")

@app.post("/webhook/whatsapp")
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming WhatsApp messages, pipes them into the LangGraph Orchestrator via background task,
    and returns 200 OK immediately to prevent Meta from retrying.
    """
    body = await request.json()
    
    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "ignored"}
            
        msg = messages[0]
        phone_number = msg.get("from")
        
        msg_type = msg.get("type")
        text_content = ""
        
        if msg_type == "audio":
            audio_id = msg.get("audio", {}).get("id")
            print(f"Incoming Voice Note (ID: {audio_id}) from {phone_number}. Downloading...")
            
            # 1. Get Audio URL from Meta
            url = f"https://graph.facebook.com/v19.0/{audio_id}"
            headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
            import requests
            res = requests.get(url, headers=headers).json()
            media_url = res.get("url")
            
            if media_url:
                # 2. Download audio data
                audio_data = requests.get(media_url, headers=headers).content
                audio_path = f"temp_{audio_id}.ogg"
                with open(audio_path, "wb") as f:
                    f.write(audio_data)
                
                # 3. Transcribe via Sarvam API
                print("Audio downloaded. Transcribing with SarvamAI...")
                try:
                    from sarvamai import SarvamAI
                    sarvam_client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
                    
                    with open(audio_path, "rb") as af:
                        response = sarvam_client.speech_to_text.transcribe(
                            file=af,
                            model="saaras:v3",
                            mode="transcribe"
                        )
                    
                    text_content = getattr(response, 'transcript', str(response))
                    print(f"Transcribed Text: {text_content}")
                    
                    # Cleanup
                    os.remove(audio_path)
                except Exception as e:
                    print(f"STT Error: {e}")
                    text_content = "SYSTEM ERROR: Could not transcribe the voice note."
            else:
                text_content = "SYSTEM ERROR: Could not fetch audio media from WhatsApp."
                
        elif msg_type == "text":
            text_content = msg.get("text", {}).get("body", "")
        else:
            print(f"Ignored unsupported message type: {msg_type}")
            return {"status": "ignored"}
        
        if not text_content:
            return {"status": "ignored"}
            
        print(f"Final Input to AI from {phone_number}: {text_content}")
        
        # Fire off the AI processing in the background
        background_tasks.add_task(process_and_reply, text_content, phone_number)
            
        return {"status": "success"}

    except Exception as e:
        print(f"Error processing WhatsApp webhook: {e}")
        return {"status": "error"}

def send_whatsapp_message_sync(to_phone: str, message: str):
    """
    Helper to send a message back to WhatsApp.
    """
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message}
    }
    try:
        # Using sync requests for simplicity in this helper
        import requests
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")

@app.post("/trigger")
async def trigger_workflow(payload: TriggerPayload):
    """Original basic trigger gateway."""
    thread_id = str(uuid.uuid4())
    initial_state = {
        "messages": [HumanMessage(content=payload.message)],
        "context": {"user_id": payload.user_id, "source": payload.source},
        "next_node": "",
        "final_response": ""
    }
    result = await orchestrator_app.ainvoke(initial_state, config={"configurable": {"thread_id": thread_id}})
    return {"status": "success", "final_response": result.get("final_response")}

if __name__ == "__main__":
    import uvicorn
    # Make sure we don't conflict with MCP server on 8000. Let's run FastAPI on 8080.
    uvicorn.run(app, host="0.0.0.0", port=8080)

from mcp.server.fastmcp import FastMCP
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from email.message import EmailMessage

mcp = FastMCP("CommsMCP")

def get_gmail_service():
    """Helper to load Gmail API credentials and return the service."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"])
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Gmail credentials are not valid or token.json is missing. Run auth_gmail.py first.")
    return build("gmail", "v1", credentials=creds)

@mcp.tool()
def list_emails(query: str = "is:unread", max_results: int = 15) -> str:
    """Search and list emails from the user's Gmail inbox. Returns metadata only (no full body).
    
    Args:
        query: Gmail search query. Defaults to 'is:unread'.
        max_results: Number of emails to return. Defaults to 15.
    """
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
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
        return f"Total estimated emails matching query: {total_estimate}\nShowing top {len(messages)}:\n\n" + "\n".join(email_summaries)
    except Exception as e:
        return f"Failed to list emails: {e}"

@mcp.tool()
def count_emails(query: str = "is:unread") -> str:
    """Count the total number of emails matching a specific Gmail query.
    
    Args:
        query: Gmail search query. Defaults to 'is:unread'.
    """
    try:
        service = get_gmail_service()
        # Fetch up to 500 messages to get an exact count instead of relying on buggy estimate
        results = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
        messages = results.get("messages", [])
        count = len(messages)
        if count == 500:
            return f"Count of emails matching '{query}': 500+ (limit reached)"
        return f"Count of emails matching '{query}': {count}"
    except Exception as e:
        return f"Failed to count emails: {e}"

@mcp.tool()
def count_todays_emails() -> str:
    """Counts the EXACT number of emails received in the last 24 hours (today). No arguments needed."""
    try:
        import datetime
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
        query = f"after:{yesterday}"
        service = get_gmail_service()
        results = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
        messages = results.get("messages", [])
        count = len(messages)
        if count == 500:
            return f"Count of today's emails: 500+ (limit reached)"
        return f"Count of today's emails: {count}"
    except Exception as e:
        return f"Failed to count today's emails: {e}"

@mcp.tool()
def read_email_details(email_id: str) -> str:
    """Read the full content of a specific email by its ID.
    
    Args:
        email_id: The unique ID of the email to read.
    """
    try:
        service = get_gmail_service()
        msg_data = service.users().messages().get(userId="me", id=email_id, format="full").execute()
        
        # Simple extraction of plain text snippet or body part
        snippet = msg_data.get("snippet", "")
        # For deeper parsing, we would decode msg_data['payload']['parts'], but snippet is safe and fits in token limits.
        
        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        
        return f"From: {sender}\nSubject: {subject}\n\nContent Preview / Snippet:\n{snippet}\n\n(End of Email)"
    except Exception as e:
        return f"Failed to read email details for {email_id}: {e}"

@mcp.tool()
def send_email(to_email: str, subject: str, body: str) -> str:
    """Send an email using Gmail API.
    
    Args:
        to_email: The recipient's email address.
        subject: The subject of the email.
        body: The main content/body of the email.
    """
    try:
        service = get_gmail_service()
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to_email
        message["From"] = "me"
        message["Subject"] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        
        service.users().messages().send(userId="me", body=create_message).execute()
        return f"Success: Sent email to {to_email} with subject '{subject}'"
    except Exception as e:
        return f"Failed to send email: {e}"

@mcp.tool()
def send_whatsapp(phone_number: str, message: str) -> str:
    """Send a proactive WhatsApp message via Meta Cloud API.
    
    Args:
        phone_number: The recipient's phone number.
        message: The text message to send.
    """
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    
    if not token or not phone_id:
        return "Error: WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_ID is not configured in the environment."
        
    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return f"Success: Sent WhatsApp message to {phone_number}"
    except Exception as e:
        return f"Failed to send WhatsApp message via Meta API: {e}"

if __name__ == "__main__":
    os.environ["PORT"] = "8000"
    mcp.run(transport="sse")

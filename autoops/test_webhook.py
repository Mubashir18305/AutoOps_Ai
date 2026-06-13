import requests

url = "http://localhost:8080/webhook/whatsapp"
params = {
    "hub.mode": "subscribe",
    "hub.challenge": "1158201444",
    "hub.verify_token": "my_secure_token_123"
}

try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.text == "1158201444":
        print("SUCCESS! The FastAPI endpoint is working perfectly.")
    else:
        print("FAILED! The response did not match the challenge.")
except Exception as e:
    print(f"ERROR: Could not connect to the server. Is it running? {e}")

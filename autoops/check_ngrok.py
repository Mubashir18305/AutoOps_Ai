import requests
try:
    response = requests.get(
        "https://headfirst-imminent-tweak.ngrok-free.dev/webhook/whatsapp",
        params={"hub.mode": "subscribe", "hub.challenge": "123", "hub.verify_token": "my_secure_token_123"}
    )
    print("STATUS:", response.status_code)
    print("TEXT:", response.text[:200])
except Exception as e:
    print("ERROR:", e)

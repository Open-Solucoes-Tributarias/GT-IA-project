import requests
import json
import os

API_URL = "http://localhost:8000/ask-legal"
API_KEY = "minha_chave_secreta_padrao"

payload = {
    "question": "Quais impostos incidem sobre a folha de pagamento?"
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

try:
    print(f"Sending request to {API_URL}...")
    response = requests.post(API_URL, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        with open("debug_output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        print(response.text)
        with open("debug_error.log", "w", encoding="utf-8") as f:
            f.write(response.text)
        
except Exception as e:
    print(f"Request failed: {e}")

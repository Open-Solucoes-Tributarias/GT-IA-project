import requests
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente (para pegar a API KEY)
load_dotenv()
API_KEY = os.getenv("GT_IA_API_KEY", "minha_chave_secreta_padrao")

URL_STATUS = "http://localhost:8000/status"
URL_ANALISE = "http://localhost:8000/analise-completa"

def test_status():
    print(f"Testando STATUS em {URL_STATUS}...")
    try:
        resp = requests.get(URL_STATUS)
        resp.raise_for_status()
        print("✅ Status Code:", resp.status_code)
        print("✅ Response:", resp.json())
    except Exception as e:
        print("❌ Erro no STATUS:", e)

def test_analise():
    print(f"\nTestando ANÁLISE em {URL_ANALISE}...")
    
    payload = {
        "company": {
            "name": "Empresa de Teste Automatizado SA",
            "cnpj": "99.999.999/0001-99",
            "activity_code": "6201-5",
            "regime": "LUCRO_PRESUMIDO"
        },
        "history": [
            {
                "period": "03/2024",
                "revenue": 500000.00,
                "payroll": 100000.00,
                "paid_amount": 40000.00,
                "paid_regime": "LUCRO_PRESUMIDO",
                "costs": {
                    "energia_eletrica": 12000.00,
                    "insumos_diretos": 150000.00,
                    "aluguel_predios": 10000.00
                }
            }
        ]
    }

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(URL_ANALISE, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("✅ Análise Sucesso!")
            print(f"💰 Economia Potencial: {data['total_savings_potential']}")
            print(f"📄 Link Download: {data['download_link']}")
        else:
            print("❌ Falha na Análise:", resp.status_code)
            print(resp.text)
    except Exception as e:
        print("❌ Erro na Requisição:", e)

if __name__ == "__main__":
    test_status()
    test_analise()

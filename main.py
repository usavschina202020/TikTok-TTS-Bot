
import sys
import requests
import os
import time
import sys  # ← ESTA LÍNEA FALTABA
from datetime import datetime

# === Cargar variables desde Railway (NO poner valores reales aquí) ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
USERNAME = os.getenv("USERNAME", "rosangelaeslo")  # cámbialo aquí si quieres otro por defecto

print("=== Bot iniciado en Railway - Versión FINAL ===")
print("Hora actual:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("Directorio actual:", os.getcwd())
print("Python versión:", sys.version.split()[0])  # ahora sí funciona
print("Variables detectadas:")
print("  - TELEGRAM_TOKEN:", "existe" if TELEGRAM_TOKEN else "FALTA")
print("  - CHAT_ID:", CHAT_ID if CHAT_ID else "FALTA")
print("  - APIFY_TOKEN:", "existe" if APIFY_TOKEN else "FALTA")
print("  - USERNAME:", USERNAME)
print("===================")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_TOKEN o CHAT_ID no configurados")
        return
    print(f"→ Enviando: {text}")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
        print(f"  Respuesta: {r.status_code} - {r.text[:100]}...")
    except Exception as e:
        print(f"  Error Telegram: {str(e)}")

def check_stories():
    print(f"Chequeando stories para: @{USERNAME}")
    if not APIFY_TOKEN:
        send_telegram("Error: APIFY_TOKEN no configurado en Railway")
        return

    url = f"https://api.apify.com/v2/acts/igview-owner~tiktok-story-viewer/runs?token={APIFY_TOKEN}&waitForFinish=60"
    payload = {"uniqueIds": [USERNAME]}
    print("Enviando petición a Apify...")
    
    try:
        r = requests.post(url, json=payload)
        print(f"  Status Apify: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print("Data Apify:", data)
            dataset_id = data.get("defaultDatasetId")
            if dataset_id:
                items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
                items = requests.get(items_url).json()
                print(f"  Stories encontradas: {len(items)}")
                
                if items:
                    send_telegram(f"¡Nueva story de @{USERNAME}! ({len(items)} stories)")
                    for item in items:
                        video_url = item.get("video_url")
                        if video_url:
                            send_telegram(f"Video: {video_url}")
                else:
                    send_telegram(f"Hoy no hay stories nuevas de @{USERNAME} 😴\nChequeo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            else:
                send_telegram("Error: No se encontró dataset en Apify")
        else:
            send_telegram(f"Error al iniciar Apify: {r.status_code}")
    except Exception as e:
        send_telegram(f"Error general: {str(e)}")

print("Iniciando bucle...")
while True:
    check_stories()
    print("Durmiendo 60 segundos (modo prueba)...")
    time.sleep(60)  # Cambia a 86400 (24 h) cuando termine de probar

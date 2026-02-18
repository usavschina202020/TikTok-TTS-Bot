import sys
import requests
import os
import time
from datetime import datetime

git add main.py
git commit -m "Agrega polling para esperar run de Apify y evita error 201"
git push



# === Cargar variables desde Railway (variables de entorno) ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
USERNAME = os.getenv("USERNAME", "nicki.nicole")  # ← aquí puedes cambiar el usuario por defecto

# Mensaje de inicio para depuración
print("=== Bot iniciado en Railway - Versión FINAL con polling ===")
print("Hora actual:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("Directorio actual:", os.getcwd())
print("Python versión:", sys.version.split()[0])
print("Variables detectadas:")
print(" - TELEGRAM_TOKEN:", "existe" if TELEGRAM_TOKEN else "FALTA")
print(" - CHAT_ID:", CHAT_ID if CHAT_ID else "FALTA")
print(" - APIFY_TOKEN:", "existe" if APIFY_TOKEN else "FALTA")
print(" - USERNAME:", USERNAME)
print("===================")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_TOKEN o CHAT_ID no configurados")
        return
    print(f"→ Enviando mensaje: {text}")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })
        print(f" Respuesta Telegram: {r.status_code} - {r.text[:100]}...")
    except Exception as e:
        print(f" Error Telegram: {str(e)}")

def check_stories():
    print(f"Chequeando stories para: @{USERNAME}")
    if not APIFY_TOKEN:
        send_telegram("Error: APIFY_TOKEN no configurado en Railway")
        return

    # 1. Lanzar el run en Apify
    url = f"https://api.apify.com/v2/acts/igview-owner~tiktok-story-viewer/runs?token={APIFY_TOKEN}"
    payload = {"uniqueIds": [USERNAME]}
    print("Enviando petición a Apify...")

    try:
        r = requests.post(url, json=payload)
        print(f" Status Apify (POST): {r.status_code}")

        if r.status_code != 201:
            send_telegram(f"Error al iniciar Apify (POST): {r.status_code} - {r.text[:200]}")
            return

        data = r.json()
        run_id = data["id"]
        print(f"Run creado, ID: {run_id}")

        # 2. Polling: esperar hasta que el run termine
        print("Esperando que el run termine...")
        dataset_id = None
        max_attempts = 40  # máximo 40 intentos = ~4 minutos
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            time.sleep(6)  # espera 6 segundos entre chequeos

            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            status_r = requests.get(status_url)
            if status_r.status_code != 200:
                print("Error chequeando status:", status_r.text)
                continue

            status_data = status_r.json()
            status = status_data["status"]
            print(f"Intento {attempt}: Status = {status}")

            if status in ["SUCCEEDED", "FINISHED"]:
                dataset_id = status_data.get("defaultDatasetId")
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                send_telegram(f"Error: El run falló en Apify (Status: {status})")
                return

        if not dataset_id:
            send_telegram("Error: El run no terminó a tiempo o no creó dataset")
            return

        # 3. Obtener los items del dataset
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
        items_r = requests.get(items_url)
        if items_r.status_code != 200:
            send_telegram(f"Error al obtener items: {items_r.status_code} - {items_r.text[:200]}")
            return

        items = items_r.json()
        print(f"Stories encontradas: {len(items)}")

        if items:
            send_telegram(f"¡Nueva story de @{USERNAME}! ({len(items)} stories)")
            for item in items:
                video_url = item.get("video_url")
                if video_url:
                    # Enviar solo el link (puedes cambiar a sendVideo si quieres el MP4 directo)
                    send_telegram(f"Video: {video_url}")
        else:
            send_telegram(f"Hoy no hay stories nuevas de @{USERNAME} 😴\nChequeo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    except Exception as e:
        send_telegram(f"Error general: {str(e)}")
        print("Excepción:", str(e))

print("Iniciando bucle...")
while True:
    check_stories()
    print("Durmiendo 86400 segundos (24 horas)...")
    time.sleep(86400)  # 24 horas - cámbialo a 60 para pruebas

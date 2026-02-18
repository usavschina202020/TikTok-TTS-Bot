import sys
import requests
import os
import time
from datetime import datetime

# Variables desde Railway
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
USERNAME = os.getenv("USERNAME", "rosangelaeslo")  # Cambia si quieres otro usuario

print("=== Bot iniciado en Railway - Versión FINAL con polling y logs mejorados ===")
print("Hora actual:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("Python versión:", sys.version.split()[0])
print("Variables:")
print(" - TELEGRAM_TOKEN:", "existe" if TELEGRAM_TOKEN else "FALTA")
print(" - CHAT_ID:", CHAT_ID if CHAT_ID else "FALTA")
print(" - APIFY_TOKEN:", "existe" if APIFY_TOKEN else "FALTA")
print(" - USERNAME:", USERNAME)
print("===================")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_TOKEN o CHAT_ID no configurados")
        return
    print(f"→ Enviando: {text}")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        })
        print(f" Telegram respuesta: {r.status_code} - {r.text[:150]}...")
    except Exception as e:
        print(f" Error enviando a Telegram: {str(e)}")

def check_stories():
    print(f"Chequeando stories para: @{USERNAME}")
    if not APIFY_TOKEN:
        send_telegram("Error: APIFY_TOKEN no configurado en Railway")
        return

    # 1. Lanzar el run
    url = f"https://api.apify.com/v2/acts/igview-owner~tiktok-story-viewer/runs?token={APIFY_TOKEN}"
    payload = {"uniqueIds": [USERNAME]}
    print("Enviando POST a Apify...")

    try:
        r = requests.post(url, json=payload)
        print(f"POST status: {r.status_code}")

        if r.status_code != 201:
            send_telegram(f"Error al iniciar run (status {r.status_code}): {r.text[:200]}")
            return

        data = r.json()
        run_id = data.get("id")
        if not run_id:
            send_telegram("Error: No se recibió run_id del POST")
            return

        print(f"Run creado: ID = {run_id}")

        # 2. Polling para esperar el run
        print("Esperando finalización del run...")
        dataset_id = None
        max_attempts = 40
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            time.sleep(6)

            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            status_r = requests.get(status_url)
            print(f"Intento {attempt} - Status code: {status_r.status_code}")

            if status_r.status_code != 200:
                print("Error chequeando status:", status_r.text[:200])
                continue

            status_data = status_r.json()
            status = status_data.get("status")
            print(f"Estado: {status}")

            if status in ["SUCCEEDED", "FINISHED"]:
                dataset_id = status_data.get("defaultDatasetId")
                if dataset_id:
                    print(f"Dataset listo: {dataset_id}")
                    break
                else:
                    send_telegram("Run terminó pero no creó dataset")
                    return
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                send_telegram(f"Run falló en Apify (Status: {status})")
                return
            else:
                print(f"Estado intermedio: {status}")

        if not dataset_id:
            send_telegram("Error: Run no terminó o no creó dataset después de 4 minutos")
            return

        # 3. Obtener items
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
        items_r = requests.get(items_url)
        print(f"GET items status: {items_r.status_code}")

        if items_r.status_code != 200:
            send_telegram(f"Error al obtener items: {items_r.status_code} - {items_r.text[:200]}")
            return

        items = items_r.json()
        print(f"Items recibidos: {len(items)}")

        if items:
            send_telegram(f"¡Nueva story de @{USERNAME}! ({len(items)} stories)")
            for item in items:
                video_url = item.get("video_url")
                if video_url:
                    send_telegram(f"Video encontrado: {video_url}")
                else:
                    send_telegram("Story encontrada pero sin video_url")
        else:
            send_telegram(f"Hoy no hay stories nuevas de @{USERNAME} 😴\nChequeo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    except Exception as e:
        error_msg = f"Error general en check_stories: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

print("Iniciando bucle infinito...")
while True:
    check_stories()
    print("Durmiendo 86400 segundos (24 horas)...")
    time.sleep(86400)  # Cambia a 60 para pruebas rápidas

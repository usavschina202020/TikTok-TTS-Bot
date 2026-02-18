import requests
import os
import time
from datetime import datetime

# Cargar variables desde Railway (NO poner valores reales aquí)
TOKEN = os.getenv("8484928881:AAFw_WDaVgws2bc7rVdmO99VKP0gv4-M11M")
CHAT_ID = os.getenv("8511189342")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
USERNAME = os.getenv("rosangelaeslo")  # cambia aquí si quieres otro por defecto

print("Bot iniciado - hora:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print(f"Variables: USERNAME={USERNAME}, CHAT_ID={CHAT_ID}, TOKEN existe={bool(TOKEN)}, APIFY_TOKEN existe={bool(APIFY_TOKEN)}")

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("Error: TOKEN o CHAT_ID no están configurados en variables de Railway")
        return
    print(f"Enviando mensaje: {text}")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
        print(f"Respuesta Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def check_stories():
    if not APIFY_TOKEN:
        send_message("Error: APIFY_TOKEN no está configurado en Railway")
        return

    print("Iniciando chequeo de stories para", USERNAME)
    url = f"https://api.apify.com/v2/acts/igview-owner~tiktok-story-viewer/runs?token={APIFY_TOKEN}&waitForFinish=60"
    payload = {"uniqueIds": [USERNAME]}
    print("Enviando petición a Apify...")
    
    try:
        r = requests.post(url, json=payload)
        print(f"Respuesta Apify status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print("Data Apify:", data)
            dataset_id = data.get("defaultDatasetId")
            if dataset_id:
                items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
                items = requests.get(items_url).json()
                print(f"Items encontrados: {len(items)}")
                
                if items:
                    send_message(f"¡Nueva story de @{USERNAME}! ({len(items)} stories)")
                    for item in items:
                        video_url = item.get("video_url")
                        if video_url:
                            send_message(f"Video: {video_url}")
                else:
                    send_message(f"Hoy no hay stories nuevas de @{USERNAME} 😴\nChequeo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            else:
                send_message("Error en Apify: no se encontró dataset ID")
        else:
            send_message(f"Error al iniciar actor Apify: {r.status_code} - {r.text}")
    except Exception as e:
        send_message(f"Error general en chequeo: {str(e)}")

print("Entrando al bucle...")
while True:
    check_stories()
    print("Durmiendo 60 segundos (prueba)...")
    time.sleep(60)  # Cambia a 86400 cuando termine de probar

import requests
import os
import time
from datetime import datetime

TOKEN = os.getenv("8484928881:AAFw_WDaVgws2bc7rVdmO99VKP0gv4-M11M")
CHAT_ID = os.getenv("8511189342")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
USERNAME = os.getenv("rosangelaeslo")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def check_stories():
    url = f"https://api.apify.com/v2/acts/igview-owner~tiktok-story-viewer/runs?token={APIFY_TOKEN}&waitForFinish=60"
    payload = {"uniqueIds": [USERNAME]}
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        data = r.json()
        dataset_id = data.get("defaultDatasetId")
        if dataset_id:
            items = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}").json()
            if items:
                send_message(f"¡Nueva story de @{USERNAME}! ({len(items)} stories)")
                for item in items:
                    video_url = item.get("video_url")
                    if video_url:
                        send_message(video_url)  # envía link, o usa sendVideo si tienes el file
            else:
                send_message(f"Hoy no hay stories nuevas de @{USERNAME} 😴\n{datetime.now().strftime('%d/%m/%Y %H:%M')}")
        else:
            send_message("Error en Apify: no dataset")
    else:
        send_message("Error al iniciar actor Apify")

while True:
    check_stories()
    time.sleep(24 * 3600)  # cada 24 horas

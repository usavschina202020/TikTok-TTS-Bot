import os
import requests
import time
import sys
from datetime import datetime

# ────────────────────────────────────────────────
# CONFIGURACIÓN (variables de entorno de Railway)
# ────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID        = os.getenv("CHAT_ID")
APIFY_TOKEN    = os.getenv("APIFY_TOKEN")
USERNAME       = os.getenv("USERNAME", "rosangelaeslo")  # puedes cambiarlo en Railway

# ────────────────────────────────────────────────
# Validación inicial (modo Batman: no fallar silenciosamente)
# ────────────────────────────────────────────────
missing = []
if not TELEGRAM_TOKEN: missing.append("TELEGRAM_TOKEN")
if not CHAT_ID:        missing.append("CHAT_ID")
if not APIFY_TOKEN:    missing.append("APIFY_TOKEN")

if missing:
    error = f"Variables faltantes: {', '.join(missing)}\nEl bot no puede funcionar sin ellas."
    print(error)
    # Intentar enviar al menos este error crítico
    if TELEGRAM_TOKEN and CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": error}
        )
    sys.exit(1)

print("╔════════════════════════════════════════════╗")
print("║       BOT STORIES TIKTOK - RAILWAY         ║")
print("║   Jimmy + Jobs + Zuck + Batman Activated   ║")
print("╚════════════════════════════════════════════╝")
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Usuario objetivo: @{USERNAME}")
print("Variables OK ✓")
print("══════════════════════════════════════════════")

def send_telegram(text: str, parse_mode: str = "Markdown"):
    """Enviar mensaje a Telegram con manejo de errores"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_notification": False
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print(f"[OK] Mensaje enviado → {text[:60]}...")
        else:
            print(f"[ERR] Telegram {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"[CRITICAL] Falló envío Telegram: {str(e)}")

def check_stories():
    """Chequeo principal de stories con polling robusto"""
    print(f"\n→ Iniciando chequeo para @{USERNAME} - {datetime.now().strftime('%H:%M:%S')}")

    # 1. Lanzar el run
    post_url = f"https://api.apify.com/v2/acts/igview-owner~tiktok-story-viewer/runs?token={APIFY_TOKEN}"
    payload = {"uniqueIds": [USERNAME]}

    try:
        r = requests.post(post_url, json=payload, timeout=15)
        if r.status_code != 201:
            send_telegram(f"❌ Error al iniciar run Apify\nStatus: {r.status_code}\n{r.text[:200]}")
            return

        data = r.json()
        run_id = data.get("id")
        if not run_id:
            send_telegram("❌ No se recibió run_id del POST")
            return

        print(f"Run lanzado → ID: {run_id}")

        # 2. Polling inteligente
        print("Esperando finalización del run...")
        dataset_id = None
        max_wait_sec = 180  # 3 minutos máximo
        sleep_sec = 5
        start_time = time.time()

        while time.time() - start_time < max_wait_sec:
            time.sleep(sleep_sec)

            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            sr = requests.get(status_url, timeout=10)

            if sr.status_code != 200:
                print(f"Error status: {sr.status_code} - {sr.text[:150]}")
                continue

            sd = sr.json()
            status = sd.get("status", "UNKNOWN")
            print(f"  Estado: {status} (tiempo transcurrido: {int(time.time() - start_time)}s)")

            if status in ["SUCCEEDED", "FINISHED"]:
                dataset_id = sd.get("defaultDatasetId")
                if dataset_id:
                    print(f"→ Dataset listo: {dataset_id}")
                    break
                else:
                    send_telegram("Run terminó pero no creó dataset")
                    return

            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                send_telegram(f"❌ Run falló en Apify\nStatus: {status}")
                return

        if not dataset_id:
            send_telegram("⏰ Run no terminó a tiempo (máx 3 min)")
            return

        # 3. Obtener stories
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
        ir = requests.get(items_url, timeout=10)

        if ir.status_code != 200:
            send_telegram(f"❌ Error al obtener stories\nStatus: {ir.status_code}\n{ir.text[:200]}")
            return

        items = ir.json()
        count = len(items)
        print(f"→ Stories encontradas: {count}")

        if count > 0:
            send_telegram(f"🔥 ¡Nueva story de @{USERNAME}! ({count} stories)")
            for item in items:
                vurl = item.get("video_url")
                if vurl:
                    send_telegram(f"🎥 Video: {vurl}")
        else:
            send_telegram(f"😴 Hoy no hay stories nuevas de @{USERNAME}\nÚltimo chequeo: {datetime.now().strftime('%d/%m %H:%M')}")

    except Exception as e:
        err = f"💥 Error crítico: {str(e)}"
        print(err)
        send_telegram(err)

# ────────────────────────────────────────────────
# BUCLE PRINCIPAL (24 horas = 86400 segundos)
# Cambia a 60 para pruebas rápidas
# ────────────────────────────────────────────────
print("Iniciando bucle infinito...")
while True:
    try:
        check_stories()
    except Exception as e:
        print(f"[CRITICAL LOOP] {str(e)}")
        send_telegram(f"Bot se cayó: {str(e)[:100]}")
    
    print(f"Durmiendo 24 horas ({time.strftime('%Y-%m-%d %H:%M:%S')})...")
    time.sleep(86400)  # ← Para pruebas rápidas: time.sleep(60)

from rtlsdr import RtlSdr
import numpy as np
import time
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import threading

load_dotenv()

# TELEGRAM BOT
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if BOT_TOKEN is None:
    raise RuntimeError("TELEGRAM_TOKEN no está definido")
CHAT_ID = os.getenv("CHAT_ID")
if CHAT_ID is None:
    raise RuntimeError("CHAT_ID no está definido")

# RF MONITORING
CENTER_FREQ = 454.975e6
SAMPLE_RATE = 250e3
SAMPLES = 64 * 1024
THRESHOLD = -37         # practical value (adjust as needed)

sdr = RtlSdr()

sdr.center_freq = CENTER_FREQ
sdr.sample_rate = SAMPLE_RATE
sdr.gain = 30

# Frequency presence check (Logic)
OFFLINE_TIMEOUT = 60 # seconds
last_seen = 0
status = None
first_run = True
previous_status = None
last_morning_report = None
last_evening_report = None
state_since = time.time()

# //// TELEGRAM ////

def send_telegram(message):

    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(
            url,
        data=data,
        timeout=10
        )
        
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Telegram error: {e}")
        if e.response is not None:
            print(e.response.text)

def telegram_listener():

    offset = None

    while True:
        url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        )

        try:
            params = {
                "timeout": 10
            }

            if offset:
                params["offset"] = offset

            response = requests.get(
                url,
                params=params,
                timeout=15
            )

            response.raise_for_status()

            updates = response.json()["result"]

            for update in updates:
                offset = update["update_id"] + 1

                if "message" not in update:
                    continue

                message = update["message"]

                chat_id = message["chat"]["id"]
                text = message.get("text", "")

                if str(chat_id) != str(CHAT_ID):
                    continue

                if text == "/alive@geocomrf_bot":
                
                    duration = time.time() - state_since
                    
                    icon = "🟢" if status == "ONLINE" else "🔴"
                    
                    if status == "ONLINE":
                        extra = f"🔄 Tiempo ONLINE: {format_duration(duration)}\n"
                    else:
                        extra = f"🔄 Tiempo OFFLINE: {format_duration(duration)}\n"
                        
                    send_telegram(
                        "✅ GEOCOM RF Monitor activo\n\n"
                        f"{icon} Estado: {status}\n"
                        f"{extra}"
                        f"📡 Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
                        f"📶 Potencia relativa: {power:.1f} dB\n"
                        f"🕒 Tiempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )

        except requests.RequestException as e:
            print(f"Telegram listener error: {e}")

        time.sleep(1)

# //// RF ////

def measure_signal():

    samples = sdr.read_samples(SAMPLES)

    power = np.mean(np.abs(samples)**2)

    power_db = 10 * np.log10(power)

    return power_db

# //// LOGS ////

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_message = f"[{timestamp}] {message}"

    print(log_message)

    with open("geocom_base.log", "a") as log:
        log.write(log_message + "\n")


def format_duration(seconds):
    seconds = int(seconds)

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def send_status_notification(status, power, timestamp, duration):

    icon = "🟢" if status == "ONLINE" else "🔴"

    message = (
        f"{icon} GEOCOM RF Monitor\n\n"
        f"Estado: {status}\n"
        f"📡 Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
        f"📶 Potencia relativa: {power:.1f} dB\n"
    )

    if status == "ONLINE":
        message += f"🔄 Tiempo OFFLINE: {format_duration(duration)}\n"
    else:
        message += f"🔄 Tiempo ONLINE: {format_duration(duration)}\n"

    message += f"🕒 Tiempo: {timestamp}"

    send_telegram(message)

# /// LOGIC ///

telegram_thread = threading.Thread(
    target=telegram_listener,
    daemon=True
)

telegram_thread.start()

try:
    while True:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        power = measure_signal()
        
        if power > THRESHOLD:
            last_seen = time.time()
            
        if time.time() - last_seen < OFFLINE_TIMEOUT:
            status = "ONLINE"
        else:
            status = "OFFLINE"
        
        if first_run:
            previous_status = status
            state_since = time.time()
            first_run = False
            
            log_event(
                f"Monitor RF inicializado\n"
                f"Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
                f"Estado actual: {status}\n"
                f"Umbral: {THRESHOLD} dB\n"
                f"Potencia relativa: {power:.1f} dB"
            )
            send_telegram(
                f"🚀 GEOCOM RF Monitor Inicializado\n\n"
                f"📡 Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
                f"Estado actual: {status}\n"
                f"📶 Potencia relativa: {power:.1f} dB\n"
                f"🕒 Tiempo: {timestamp}"
            )
        elif status != previous_status:
            
            duration = time.time() - state_since
            
            log_event(
                f"GEOCOM BASE {status}\n"
                f"Tiempo en estado anterior: {format_duration(duration)}\n"
                f"Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
                f"Potencia relativa: {power:.1f} dB"
            )

            send_status_notification(
                status,
                power,
                timestamp,
                duration
            )
            
            state_since = time.time()
            previous_status = status
            
        if (now.hour == 8 and now.minute == 0 and last_morning_report != now.date()):
            send_telegram(
                f"🌅 GEOCOM RF Monitor\n"
                f"Reporte diario - 8:00 AM\n\n"
                f"Fecha: {now.strftime('%Y-%m-%d %H:%M')}\n"
                f"Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
                f"Estado: {'🟢 ONLINE' if status == 'ONLINE' else '🔴 OFFLINE'}\n"
                f"Potencia: {power:.1f} dB\n"
                f"Umbral: {THRESHOLD:.1f} dB"
            )
            
            last_morning_report = now.date()
        
        time.sleep(0.2)


except KeyboardInterrupt:
    pass

finally:
    sdr.close()

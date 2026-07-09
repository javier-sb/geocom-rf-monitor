from rtlsdr import RtlSdr
import numpy as np
import time
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

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
THRESHOLD = -33         # practical value (with antenna, then without antenna while base is transmitting) --> (-45.1 + -21.8) / 2 = -33.45 dB

sdr = RtlSdr()

sdr.center_freq = CENTER_FREQ
sdr.sample_rate = SAMPLE_RATE
sdr.gain = 30

# Frequency presence check (Logic)
OFFLINE_TIMEOUT = 5 # seconds
last_seen = 0
status = None
first_run = True
previous_status = None

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
        requests.post(
            url,
            data=data,
            timeout=10
        )
    except requests.RequestException as e:
        print(f"Telegram error: {e}")

# //// RF ////

def measure_signal():

    samples = sdr.read_samples(SAMPLES)

    power = np.mean(np.abs(samples)**2)

    power_db = 10 * np.log10(power)

    return power_db


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_message = f"[{timestamp}] {message}"

    print(log_message)
    send_telegram(log_message)

    with open("geocom_base.log", "a") as log:
        log.write(log_message + "\n")

# /// LOGIC ///

try:
    while True:

        power = measure_signal()
        
        if power > THRESHOLD:
            last_seen = time.time()
            
        if time.time() - last_seen < OFFLINE_TIMEOUT:
            status = "ONLINE"
        else:
            status = "OFFLINE"
        
        if first_run:
            previous_status = status
            first_run = False
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_event(
                f"Monitor RF inicializado\n"
                f"Frecuencia: {CENTER_FREQ/1e6:.3f} MHz\n"
                f"Estado actual: {status}\n"
                f"Umbral: {THRESHOLD} dB\n"
                f"Potencia relativa: {power:.1f} dB"
            ) 
        elif status != previous_status:
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if status == "ONLINE":
                log_event(
                    f"GEOCOM BASE DETECTADA (454.975 MHz)\n"
                    f"Potencia relativa: {power:.1f} dB"
                )
            else:
                log_event(
                    f"GEOCOM BASE NO DETECTADA (454.975 MHz)\n"
                    f"Potencia relativa: {power:.1f} dB"
                )
                
            previous_status = status

        time.sleep(1)


except KeyboardInterrupt:
    pass

finally:
    sdr.close()

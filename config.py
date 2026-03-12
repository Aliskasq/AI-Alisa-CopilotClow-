import json
import logging
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables from .env file
load_dotenv()

# Telegram Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROUP_CHAT_ID = os.getenv("TELEGRAM_GROUP_CHAT_ID")

# AI Service configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")

# Binance Square
SQUARE_OPENAPI_KEY = os.getenv("SQUARE_OPENAPI_KEY")

# Encryption setup for Binance API keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "").encode()
ENCRYPTED_API_KEY = os.getenv("ENCRYPTED_API_KEY", "").encode()
ENCRYPTED_SECRET_KEY = os.getenv("ENCRYPTED_SECRET_KEY", "").encode()

if ENCRYPTION_KEY and ENCRYPTED_API_KEY and ENCRYPTED_SECRET_KEY:
    fernet = Fernet(ENCRYPTION_KEY)
    BINANCE_API_KEY = fernet.decrypt(ENCRYPTED_API_KEY).decode()
    BINANCE_SECRET_KEY = fernet.decrypt(ENCRYPTED_SECRET_KEY).decode()
else:
    BINANCE_API_KEY = None
    BINANCE_SECRET_KEY = None

TREND_STATE_FILE = "data/trend_state.json"
ALERTS_FILE = "data/pending_alerts.json"

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading alerts file: {e}")
    return []

def save_alerts(alerts):
    try:
        with open(ALERTS_FILE, "w") as f:
            json.dump(alerts, f, indent=4)
    except Exception as e:
        logging.error(f"Error writing alerts file: {e}")

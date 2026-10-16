import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_PATH = BASE_DIR / "fuelbot.db"

# Мережі АЗС та доступні види пального
NETWORKS = {
    "wog": {"name": "WOG", "icon": "🟢", "scen": "qr_download"},
    "okko": {"name": "OKKO", "icon": "🟡", "scen": "pump_photo"},
    "ukrnafta": {"name": "Ukrnafta", "icon": "🔵", "scen": "qr_download"},
}

FUEL_TYPES = {
    "a95": "Бензин А-95",
    "dp": "Дизельне пальне (ДП)",
    "gas": "Газ (LPG)"
}

PAYMENT_METHODS = {
    "tov": {
        "title": "Розрахунковий рахунок ТОВ",
        "badge": "Безготівковий (з ПДВ)",
        "currency": "UAH",
        "rate_mod": 1.05
    },
    "fop": {
        "title": "Підприємницький рахунок ФОП",
        "badge": "Вигідна ціна UAH",
        "currency": "UAH",
        "rate_mod": 1.00
    },
    "usdt": {
        "title": "USDT (TRC20)",
        "badge": "Найнижча ціна",
        "currency": "USDT",
        "rate_mod": 0.96
    }
}

DEFAULT_NOMINALS = [10, 20, 30, 50]
USDT_RATE = 41.50

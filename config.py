from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "database" / "hostel.db")
SECRET_KEY = "hostelerp-secret"
# ==============================
# POCKET MONEY CONFIG
# ==============================
POCKET_MONEY_MIN_BALANCE_FOR_GATEPASS = 200

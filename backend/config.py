import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ssl_disabled = os.getenv("DB_SSL_DISABLED", "true").lower() in ("1", "true", "yes")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "obras"),
    "password": os.getenv("DB_PASSWORD", "obras123"),
    "database": os.getenv("DB_NAME", "obras"),
    "charset": "utf8mb4",
    "autocommit": True,
    "ssl_disabled": ssl_disabled,
    "consume_results": True,
}

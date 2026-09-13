import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

WEAK_SECRET_KEYS = {
    "dev-secret-key-change-me",
    "chave_secreta_padrao_para_desenvolvimento",
}

ENV = os.getenv("ENV", "dev").strip().lower()
SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY é obrigatória. Defina no .env")
if ENV != "dev" and SECRET_KEY in WEAK_SECRET_KEYS:
    raise RuntimeError("SECRET_KEY padrão não é permitida fora de ENV=dev")

_DEFAULT_CORS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_CORS).split(",")
    if origin.strip()
]

INTERNAL_ERROR = "Erro interno. Tente novamente."
UPLOADS_DIR = BASE_DIR / "uploads" / "comprovantes"
MAX_RECEIPT_BYTES = 5 * 1024 * 1024

ssl_disabled = os.getenv("DB_SSL_DISABLED", "true").lower() in ("1", "true", "yes")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "obras"),
    "password": os.getenv("DB_PASSWORD", "obras123"),
    "database": os.getenv("DB_NAME", "obras"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "use_unicode": True,
    "autocommit": True,
    "ssl_disabled": ssl_disabled,
    "consume_results": True,
}

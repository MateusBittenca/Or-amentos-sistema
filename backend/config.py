import os
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurar o logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuração do banco de dados
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "turntable.proxy.rlwy.net"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "SpDrzzWjYjYcvQDrlOldHkKLKMmmJRbt"),
    "database": os.getenv("DB_NAME", "railway"),
    "port": int(os.getenv("DB_PORT", "10713")),
}
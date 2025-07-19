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
    "host": "34.44.96.177",  # IP público da instância Cloud SQL
    "port": 3306,
    "user": "Mateus",
    "password": "RI3eh9N9:4f.|`ip",
    "database": "obras",
    "charset": "utf8mb4",
    "autocommit": True,
    "ssl_disabled": False,  # SSL habilitado por padrão no Cloud SQL
    "consume_results": True  # Consumir resultados automaticamente
}
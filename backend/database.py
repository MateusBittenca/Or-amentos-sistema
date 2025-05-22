import mysql.connector
from mysql.connector import Error, pooling
from fastapi import HTTPException
from config import DB_CONFIG, logger

# Criar o pool de conexões
connection_pool = None

def init_connection_pool():
    """Inicializar o pool de conexões"""
    global connection_pool
    try:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="obra_pool",
            pool_size=10,
            **DB_CONFIG
        )
        logger.info("Pool de conexões inicializado com sucesso")
    except Error as e:
        logger.error(f"Erro ao inicializar o pool de conexões MySQL: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na inicialização do pool: {str(e)}")

def get_db_connection():
    """Obter uma conexão do pool"""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()
        
    try:
        connection = connection_pool.get_connection()
        return connection
    except Error as e:
        logger.error(f"Erro ao obter conexão do pool: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão com o banco de dados: {str(e)}")

def initialize_database():
    """Inicializar tabelas do banco de dados se não existirem"""
    try:
        # Inicializar o pool de conexões
        init_connection_pool()
        
        connection = get_db_connection()
        cursor = connection.cursor()

        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Banco de dados inicializado com sucesso")
    except Error as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de inicialização do banco de dados: {str(e)}")
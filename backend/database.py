import mysql.connector
from mysql.connector import Error
from fastapi import HTTPException
from config import DB_CONFIG, logger

def get_db_connection():
    """Criar e retornar uma conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Erro ao conectar ao banco de dados MySQL: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão com o banco de dados: {str(e)}")

def initialize_database():
    """Inicializar tabelas do banco de dados se não existirem"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Banco de dados inicializado com sucesso")
    except Error as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de inicialização do banco de dados: {str(e)}")
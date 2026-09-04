import mysql.connector
from mysql.connector import Error, pooling
from fastapi import HTTPException
from config import DB_CONFIG, logger

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
        return connection_pool.get_connection()
    except Error as e:
        logger.error(f"Erro ao obter conexão do pool: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão com o banco de dados: {str(e)}")


def _column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
        """,
        (table, column),
    )
    return cursor.fetchone()[0] > 0


def _table_exists(cursor, table):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        (table,),
    )
    return cursor.fetchone()[0] > 0


def initialize_database():
    """Criar tabelas, migrar schema legado e garantir seed."""
    try:
        from auth.passwords import hash_password, is_hashed

        init_connection_pool()
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'USER',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS obras (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                descricao TEXT,
                criado_por INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (criado_por) REFERENCES usuarios(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS obra_membros (
                id INT AUTO_INCREMENT PRIMARY KEY,
                obra_id INT NOT NULL,
                usuario_id INT NOT NULL,
                papel VARCHAR(20) NOT NULL DEFAULT 'membro',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_obra_usuario (obra_id, usuario_id),
                FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atividades (
                idAtividades INT AUTO_INCREMENT PRIMARY KEY,
                obra_id INT DEFAULT NULL,
                nome VARCHAR(255) NOT NULL,
                setor VARCHAR(255) DEFAULT NULL,
                valor DECIMAL(12, 2) NOT NULL,
                data VARCHAR(20) DEFAULT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE
            )
        """)

        if not _column_exists(cursor, "atividades", "obra_id"):
            cursor.execute("ALTER TABLE atividades ADD COLUMN obra_id INT DEFAULT NULL")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                atividade_id INT NOT NULL,
                usuario_id INT NOT NULL,
                valor DECIMAL(12, 2) NOT NULL,
                data VARCHAR(20) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (atividade_id) REFERENCES atividades(idAtividades) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS convites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                obra_id INT NOT NULL,
                token VARCHAR(64) NOT NULL UNIQUE,
                papel VARCHAR(20) NOT NULL DEFAULT 'membro',
                email VARCHAR(255) DEFAULT NULL,
                expira_em DATETIME NOT NULL,
                usado_em DATETIME DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("SELECT id, password FROM usuarios")
        for user_id, password in cursor.fetchall():
            if password and not is_hashed(password):
                cursor.execute(
                    "UPDATE usuarios SET password = %s WHERE id = %s",
                    (hash_password(password), user_id),
                )

        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO usuarios (nome, password, status) VALUES (%s, %s, %s)",
                ("admin@local.com", hash_password("admin123"), "USER"),
            )

        cursor.execute("SELECT id FROM usuarios WHERE LOWER(nome) = LOWER(%s)", ("admin@local.com",))
        admin_row = cursor.fetchone()
        admin_id = admin_row[0] if admin_row else None

        if admin_id:
            cursor.execute("SELECT id FROM obras LIMIT 1")
            obra_row = cursor.fetchone()
            if not obra_row:
                cursor.execute(
                    "INSERT INTO obras (nome, descricao, criado_por) VALUES (%s, %s, %s)",
                    ("Obra existente", "Dados migrados do sistema anterior", admin_id),
                )
                obra_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO obra_membros (obra_id, usuario_id, papel) VALUES (%s, %s, %s)",
                    (obra_id, admin_id, "owner"),
                )
            else:
                obra_id = obra_row[0]
                cursor.execute(
                    "SELECT id FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
                    (obra_id, admin_id),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO obra_membros (obra_id, usuario_id, papel) VALUES (%s, %s, %s)",
                        (obra_id, admin_id, "owner"),
                    )

            cursor.execute("UPDATE atividades SET obra_id = %s WHERE obra_id IS NULL", (obra_id,))

            has_diego = _column_exists(cursor, "atividades", "diego_ana")
            has_alex = _column_exists(cursor, "atividades", "alex_rute")
            if has_diego or has_alex:
                cursor.execute("SELECT COUNT(*) FROM pagamentos")
                if cursor.fetchone()[0] == 0:
                    select_cols = ["idAtividades"]
                    if has_diego:
                        select_cols.append("COALESCE(diego_ana, 0)")
                    if has_alex:
                        select_cols.append("COALESCE(alex_rute, 0)")
                    if has_diego and has_alex:
                        cursor.execute(
                            f"SELECT {', '.join(select_cols)}, data FROM atividades"
                        )
                        for row in cursor.fetchall():
                            atividade_id, diego, alex, data = row
                            total = float(diego or 0) + float(alex or 0)
                            if total > 0:
                                cursor.execute(
                                    "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                                    (atividade_id, admin_id, total, data),
                                )
                    elif has_diego:
                        cursor.execute("SELECT idAtividades, COALESCE(diego_ana, 0), data FROM atividades")
                        for atividade_id, diego, data in cursor.fetchall():
                            if float(diego or 0) > 0:
                                cursor.execute(
                                    "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                                    (atividade_id, admin_id, diego, data),
                                )
                    elif has_alex:
                        cursor.execute("SELECT idAtividades, COALESCE(alex_rute, 0), data FROM atividades")
                        for atividade_id, alex, data in cursor.fetchall():
                            if float(alex or 0) > 0:
                                cursor.execute(
                                    "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                                    (atividade_id, admin_id, alex, data),
                                )

                if has_diego:
                    cursor.execute("ALTER TABLE atividades DROP COLUMN diego_ana")
                if has_alex:
                    cursor.execute("ALTER TABLE atividades DROP COLUMN alex_rute")

            cursor.execute("SELECT COUNT(*) FROM atividades WHERE obra_id = %s", (obra_id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """
                    INSERT INTO atividades (obra_id, nome, valor, data, setor, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (obra_id, "Projeto estrutural", 5000.00, "15/03/2024", "Projeto", "paid"),
                )
                atividade_paga_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                    (atividade_paga_id, admin_id, 5000.00, "15/03/2024"),
                )
                cursor.execute(
                    """
                    INSERT INTO atividades (obra_id, nome, valor, data, setor, status)
                    VALUES (%s, %s, %s, %s, %s, %s),
                           (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        obra_id, "Cimento 50kg x 20", 1800.00, "20/03/2024", "Cimento e Concreto", "pending",
                        obra_id, "Instalação elétrica 1º andar", 3200.00, "01/04/2024", "Elétrica", "pending",
                    ),
                )

            cursor.execute("""
                UPDATE atividades a
                SET status = CASE
                    WHEN COALESCE((SELECT SUM(p.valor) FROM pagamentos p WHERE p.atividade_id = a.idAtividades), 0) >= a.valor
                    THEN 'paid' ELSE 'pending'
                END
            """)

        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Banco de dados inicializado com sucesso")
    except Error as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de inicialização do banco de dados: {str(e)}")

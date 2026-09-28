from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error, pooling
from fastapi import HTTPException
from config import DB_CONFIG, ENV, INTERNAL_ERROR, UPLOADS_DIR, logger

connection_pool = None

DISPLAY_NAME_SQL = "COALESCE(NULLIF(TRIM(u.nome_exibicao), ''), u.nome)"
UTF8_TABLES = ("usuarios", "obras", "obra_membros", "atividades", "pagamentos", "convites", "atividade_participacoes")
MOJIBAKE_MARKERS = ("Ã", "Â", "â€")


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
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR)


def get_db_connection():
    """Obter uma conexão do pool"""
    global connection_pool
    if connection_pool is None:
        init_connection_pool()

    try:
        connection = connection_pool.get_connection()
        try:
            connection.set_charset_collation("utf8mb4", "utf8mb4_unicode_ci")
        except Exception:
            pass
        return connection
    except Error as e:
        logger.error(f"Erro ao obter conexão do pool: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR)


@contextmanager
def db_cursor(dictionary=True):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield cursor
        connection.commit()
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass


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


def _repair_mojibake(value):
    if not value or not isinstance(value, str):
        return value
    if not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return value


def _table_charset(cursor, table):
    cursor.execute(
        """
        SELECT CCSA.character_set_name
        FROM information_schema.TABLES T
        JOIN information_schema.COLLATION_CHARACTER_SET_APPLICABILITY CCSA
          ON CCSA.collation_name = T.TABLE_COLLATION
        WHERE T.TABLE_SCHEMA = DATABASE() AND T.TABLE_NAME = %s
        """,
        (table,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _ensure_utf8mb4_tables(cursor):
    for table in UTF8_TABLES:
        if not _table_exists(cursor, table):
            continue
        if _table_charset(cursor, table) == "utf8mb4":
            continue
        cursor.execute(
            f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )


def _repair_mojibake_columns(cursor):
    targets = (
        ("atividades", "idAtividades", ("nome", "setor")),
        ("obras", "id", ("nome", "descricao")),
    )
    for table, pk, columns in targets:
        if not _table_exists(cursor, table):
            continue
        col_sql = ", ".join((pk,) + columns)
        cursor.execute(f"SELECT {col_sql} FROM `{table}`")
        rows = cursor.fetchall()
        for row in rows:
            pk_val = row[0]
            updates = []
            values = []
            for index, column in enumerate(columns):
                original = row[index + 1]
                repaired = _repair_mojibake(original)
                if repaired != original:
                    updates.append(f"`{column}` = %s")
                    values.append(repaired)
            if updates:
                values.append(pk_val)
                cursor.execute(
                    f"UPDATE `{table}` SET {', '.join(updates)} WHERE `{pk}` = %s",
                    values,
                )


def _backfill_participacoes(cursor):
    """Congela participação igual nas obras e atividades que ainda não têm rateio."""
    if not _table_exists(cursor, "atividade_participacoes"):
        return
    if not _column_exists(cursor, "obra_membros", "participacao"):
        return
    cursor.execute("SELECT id FROM obras")
    obra_ids = [row[0] for row in cursor.fetchall()]
    for obra_id in obra_ids:
        cursor.execute(
            """
            SELECT usuario_id, papel, participacao
            FROM obra_membros
            WHERE obra_id = %s
            ORDER BY usuario_id
            """,
            (obra_id,),
        )
        members = cursor.fetchall()
        participating = [member for member in members if member[1] != "leitura"]
        if participating and all(member[2] is None for member in participating):
            count = len(participating)
            base, rem = divmod(10000, count)
            for index, member in enumerate(participating):
                percentual = (base + (1 if index < rem else 0)) / 100.0
                cursor.execute(
                    "UPDATE obra_membros SET participacao = %s WHERE obra_id = %s AND usuario_id = %s",
                    (percentual, obra_id, member[0]),
                )
        cursor.execute(
            """
            SELECT a.idAtividades
            FROM atividades a
            WHERE a.obra_id = %s
              AND NOT EXISTS (
                  SELECT 1 FROM atividade_participacoes ap
                  WHERE ap.atividade_id = a.idAtividades
              )
            """,
            (obra_id,),
        )
        activity_ids = [row[0] for row in cursor.fetchall()]
        if not activity_ids:
            continue
        cursor.execute(
            """
            SELECT usuario_id, participacao
            FROM obra_membros
            WHERE obra_id = %s AND papel <> 'leitura' AND participacao IS NOT NULL
            ORDER BY usuario_id
            """,
            (obra_id,),
        )
        shares = cursor.fetchall()
        if not shares:
            continue
        for atividade_id in activity_ids:
            for usuario_id, percentual in shares:
                cursor.execute(
                    """
                    INSERT INTO atividade_participacoes (atividade_id, usuario_id, percentual)
                    VALUES (%s, %s, %s)
                    """,
                    (atividade_id, usuario_id, percentual),
                )


def initialize_database():
    """Criar tabelas, migrar schema legado e garantir seed."""
    try:
        from auth.passwords import hash_password, is_hashed

        init_connection_pool()
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
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
                comprovante_url VARCHAR(500) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (atividade_id) REFERENCES atividades(idAtividades) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)

        if not _column_exists(cursor, "pagamentos", "comprovante_url"):
            cursor.execute("ALTER TABLE pagamentos ADD COLUMN comprovante_url VARCHAR(500) DEFAULT NULL")

        if not _column_exists(cursor, "usuarios", "nome_exibicao"):
            cursor.execute("ALTER TABLE usuarios ADD COLUMN nome_exibicao VARCHAR(255) DEFAULT NULL")

        if not _column_exists(cursor, "obra_membros", "participacao"):
            cursor.execute("ALTER TABLE obra_membros ADD COLUMN participacao DECIMAL(5, 2) DEFAULT NULL")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atividade_participacoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                atividade_id INT NOT NULL,
                usuario_id INT NOT NULL,
                percentual DECIMAL(5, 2) NOT NULL,
                UNIQUE KEY unique_atividade_usuario (atividade_id, usuario_id),
                FOREIGN KEY (atividade_id) REFERENCES atividades(idAtividades) ON DELETE CASCADE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)

        _ensure_utf8mb4_tables(cursor)
        _repair_mojibake_columns(cursor)

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
        user_count = cursor.fetchone()[0]
        if ENV == "dev" and user_count == 0:
            cursor.execute(
                "INSERT INTO usuarios (nome, password, status) VALUES (%s, %s, %s)",
                ("admin@local.com", hash_password("admin123"), "USER"),
            )
            admin_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO obras (nome, descricao, criado_por) VALUES (%s, %s, %s)",
                ("Obra existente", "Dados migrados do sistema anterior", admin_id),
            )
            obra_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO obra_membros (obra_id, usuario_id, papel) VALUES (%s, %s, %s)",
                (obra_id, admin_id, "owner"),
            )
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

        cursor.execute("SELECT id FROM obras LIMIT 1")
        obra_row = cursor.fetchone()
        if obra_row:
            cursor.execute("UPDATE atividades SET obra_id = %s WHERE obra_id IS NULL", (obra_row[0],))

        cursor.execute("SELECT id FROM usuarios LIMIT 1")
        payer_row = cursor.fetchone()
        payer_id = payer_row[0] if payer_row else None

        has_diego = _column_exists(cursor, "atividades", "diego_ana")
        has_alex = _column_exists(cursor, "atividades", "alex_rute")
        if has_diego or has_alex:
            cursor.execute("SELECT COUNT(*) FROM pagamentos")
            if payer_id and cursor.fetchone()[0] == 0:
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
                                (atividade_id, payer_id, total, data),
                            )
                elif has_diego:
                    cursor.execute("SELECT idAtividades, COALESCE(diego_ana, 0), data FROM atividades")
                    for atividade_id, diego, data in cursor.fetchall():
                        if float(diego or 0) > 0:
                            cursor.execute(
                                "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                                (atividade_id, payer_id, diego, data),
                            )
                elif has_alex:
                    cursor.execute("SELECT idAtividades, COALESCE(alex_rute, 0), data FROM atividades")
                    for atividade_id, alex, data in cursor.fetchall():
                        if float(alex or 0) > 0:
                            cursor.execute(
                                "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                                (atividade_id, payer_id, alex, data),
                            )
            if has_diego:
                cursor.execute("ALTER TABLE atividades DROP COLUMN diego_ana")
            if has_alex:
                cursor.execute("ALTER TABLE atividades DROP COLUMN alex_rute")

        cursor.execute("""
            UPDATE atividades a
            SET status = CASE
                WHEN COALESCE((SELECT SUM(p.valor) FROM pagamentos p WHERE p.atividade_id = a.idAtividades), 0) >= a.valor
                THEN 'paid' ELSE 'pending'
            END
        """)

        _backfill_participacoes(cursor)

        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Banco de dados inicializado com sucesso")
    except Error as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR)

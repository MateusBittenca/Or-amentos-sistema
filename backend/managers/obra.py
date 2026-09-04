from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import secrets
from fastapi import HTTPException
from config import logger
from database import get_db_connection
from models import ObraOut, MembroOut
from auth.auth_user import assert_obra_access, ROLE_RANK


class ObrasManager:
    def listar_minhas_obras(self, usuario_id: int) -> List[ObraOut]:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT o.id, o.nome, o.descricao, o.criado_por, om.papel
            FROM obras o
            JOIN obra_membros om ON om.obra_id = o.id
            WHERE om.usuario_id = %s
            ORDER BY o.created_at DESC
            """,
            (usuario_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return [
            ObraOut(
                id=row["id"],
                nome=row["nome"],
                descricao=row.get("descricao"),
                papel=row["papel"],
                criado_por=row["criado_por"],
            )
            for row in rows
        ]

    def obter_obra(self, obra_id: int, usuario_id: int) -> ObraOut:
        membership = assert_obra_access(obra_id, usuario_id, "leitura")
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, descricao, criado_por FROM obras WHERE id = %s", (obra_id,))
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if not row:
            raise HTTPException(status_code=404, detail="Obra não encontrada")
        return ObraOut(
            id=row["id"],
            nome=row["nome"],
            descricao=row.get("descricao"),
            papel=membership["papel"],
            criado_por=row["criado_por"],
        )

    def criar_obra(self, usuario_id: int, nome: str, descricao: Optional[str] = None) -> ObraOut:
        nome = (nome or "").strip()
        if not nome:
            raise HTTPException(status_code=400, detail="O nome da obra é obrigatório")

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO obras (nome, descricao, criado_por) VALUES (%s, %s, %s)",
            (nome, descricao, usuario_id),
        )
        obra_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO obra_membros (obra_id, usuario_id, papel) VALUES (%s, %s, %s)",
            (obra_id, usuario_id, "owner"),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return ObraOut(
            id=obra_id,
            nome=nome,
            descricao=descricao,
            papel="owner",
            criado_por=usuario_id,
        )

    def listar_membros(self, obra_id: int, usuario_id: int) -> List[MembroOut]:
        assert_obra_access(obra_id, usuario_id, "leitura")
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT om.usuario_id, u.nome, om.papel
            FROM obra_membros om
            JOIN usuarios u ON u.id = om.usuario_id
            WHERE om.obra_id = %s
            ORDER BY FIELD(om.papel, 'owner', 'editor', 'membro', 'leitura'), u.nome
            """,
            (obra_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return [
            MembroOut(usuario_id=row["usuario_id"], nome=row["nome"], papel=row["papel"])
            for row in rows
        ]

    def criar_convite(self, obra_id: int, usuario_id: int, papel: str = "membro", email: Optional[str] = None) -> Dict[str, Any]:
        assert_obra_access(obra_id, usuario_id, "editor")
        if papel not in ROLE_RANK or papel == "owner":
            raise HTTPException(status_code=400, detail="Papel de convite inválido")

        token = secrets.token_urlsafe(24)
        expira_em = datetime.utcnow() + timedelta(days=7)

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO convites (obra_id, token, papel, email, expira_em)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (obra_id, token, papel, email, expira_em),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return {
            "sucesso": True,
            "token": token,
            "papel": papel,
            "expira_em": expira_em.isoformat(),
            "url": f"/convite/{token}",
        }

    def obter_convite(self, token: str) -> Dict[str, Any]:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.id, c.obra_id, c.papel, c.expira_em, c.usado_em, o.nome as obra_nome
            FROM convites c
            JOIN obras o ON o.id = c.obra_id
            WHERE c.token = %s
            """,
            (token,),
        )
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if not row:
            raise HTTPException(status_code=404, detail="Convite não encontrado")
        if row["usado_em"]:
            raise HTTPException(status_code=400, detail="Este convite já foi utilizado")
        if row["expira_em"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Este convite expirou")
        return {
            "obra_id": row["obra_id"],
            "obra_nome": row["obra_nome"],
            "papel": row["papel"],
            "expira_em": row["expira_em"].isoformat() if row["expira_em"] else None,
        }

    def aceitar_convite(self, token: str, usuario_id: int) -> Dict[str, Any]:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, obra_id, papel, expira_em, usado_em FROM convites WHERE token = %s",
            (token,),
        )
        convite = cursor.fetchone()
        if not convite:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=404, detail="Convite não encontrado")
        if convite["usado_em"]:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="Este convite já foi utilizado")
        if convite["expira_em"] < datetime.utcnow():
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="Este convite expirou")

        cursor.execute(
            "SELECT id FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
            (convite["obra_id"], usuario_id),
        )
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                "INSERT INTO obra_membros (obra_id, usuario_id, papel) VALUES (%s, %s, %s)",
                (convite["obra_id"], usuario_id, convite["papel"]),
            )
        cursor.execute(
            "UPDATE convites SET usado_em = %s WHERE id = %s",
            (datetime.utcnow(), convite["id"]),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return {
            "sucesso": True,
            "obra_id": convite["obra_id"],
            "papel": convite["papel"],
            "mensagem": "Você entrou na obra",
        }

    def atualizar_papel(self, obra_id: int, owner_id: int, membro_id: int, papel: str) -> Dict[str, Any]:
        assert_obra_access(obra_id, owner_id, "owner")
        if papel not in ROLE_RANK:
            raise HTTPException(status_code=400, detail="Papel inválido")
        if membro_id == owner_id:
            raise HTTPException(status_code=400, detail="Você não pode alterar o próprio papel")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT papel FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
            (obra_id, membro_id),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=404, detail="Membro não encontrado")
        if row["papel"] == "owner":
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="Não é possível alterar o dono da obra")

        cursor.execute(
            "UPDATE obra_membros SET papel = %s WHERE obra_id = %s AND usuario_id = %s",
            (papel, obra_id, membro_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return {"sucesso": True, "mensagem": "Papel atualizado"}

    def remover_membro(self, obra_id: int, owner_id: int, membro_id: int) -> Dict[str, Any]:
        assert_obra_access(obra_id, owner_id, "owner")
        if membro_id == owner_id:
            raise HTTPException(status_code=400, detail="Você não pode remover a si mesmo")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT papel FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
            (obra_id, membro_id),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            connection.close()
            raise HTTPException(status_code=404, detail="Membro não encontrado")
        if row["papel"] == "owner":
            cursor.close()
            connection.close()
            raise HTTPException(status_code=400, detail="Não é possível remover o dono da obra")

        cursor.execute(
            "DELETE FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
            (obra_id, membro_id),
        )
        connection.commit()
        cursor.close()
        connection.close()
        return {"sucesso": True, "mensagem": "Membro removido da obra"}

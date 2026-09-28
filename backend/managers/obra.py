from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import secrets
from fastapi import HTTPException
from database import DISPLAY_NAME_SQL, db_cursor
from models import ObraOut, MembroOut, ParticipacaoItem
from auth.auth_user import assert_obra_access, ROLE_RANK
from managers.comprovante import percentuais_iguais, validar_percentuais

PAPEIS_RATEIO = {"owner", "editor", "membro"}


def rebalance_participacao(cursor, obra_id: int) -> None:
    cursor.execute(
        """
        SELECT usuario_id FROM obra_membros
        WHERE obra_id = %s AND papel <> 'leitura'
        ORDER BY usuario_id
        """,
        (obra_id,),
    )
    ids = [row["usuario_id"] for row in cursor.fetchall()]
    cursor.execute(
        "UPDATE obra_membros SET participacao = NULL WHERE obra_id = %s AND papel = 'leitura'",
        (obra_id,),
    )
    for usuario_id, percentual in zip(ids, percentuais_iguais(len(ids))):
        cursor.execute(
            "UPDATE obra_membros SET participacao = %s WHERE obra_id = %s AND usuario_id = %s",
            (percentual, obra_id, usuario_id),
        )


class ObrasManager:
    def listar_minhas_obras(self, usuario_id: int) -> List[ObraOut]:
        with db_cursor() as cursor:
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
        with db_cursor() as cursor:
            cursor.execute("SELECT id, nome, descricao, criado_por FROM obras WHERE id = %s", (obra_id,))
            row = cursor.fetchone()
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

        with db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO obras (nome, descricao, criado_por) VALUES (%s, %s, %s)",
                (nome, descricao, usuario_id),
            )
            obra_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO obra_membros (obra_id, usuario_id, papel, participacao) VALUES (%s, %s, %s, %s)",
                (obra_id, usuario_id, "owner", 100),
            )
        return ObraOut(
            id=obra_id,
            nome=nome,
            descricao=descricao,
            papel="owner",
            criado_por=usuario_id,
        )

    def listar_membros(self, obra_id: int, usuario_id: int) -> List[MembroOut]:
        assert_obra_access(obra_id, usuario_id, "leitura")
        with db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT om.usuario_id, {DISPLAY_NAME_SQL} as nome, om.papel, om.participacao
                FROM obra_membros om
                JOIN usuarios u ON u.id = om.usuario_id
                WHERE om.obra_id = %s
                ORDER BY FIELD(om.papel, 'owner', 'editor', 'membro', 'leitura'), nome
                """,
                (obra_id,),
            )
            rows = cursor.fetchall()
        return [
            MembroOut(
                usuario_id=row["usuario_id"],
                nome=row["nome"],
                papel=row["papel"],
                participacao=float(row["participacao"]) if row["participacao"] is not None else None,
            )
            for row in rows
        ]

    def criar_convite(self, obra_id: int, usuario_id: int, papel: str = "membro", email: Optional[str] = None) -> Dict[str, Any]:
        assert_obra_access(obra_id, usuario_id, "editor")
        if papel not in ROLE_RANK or papel == "owner":
            raise HTTPException(status_code=400, detail="Papel de convite inválido")

        token = secrets.token_urlsafe(24)
        expira_em = datetime.utcnow() + timedelta(days=7)

        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO convites (obra_id, token, papel, email, expira_em)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (obra_id, token, papel, email, expira_em),
            )
        return {
            "sucesso": True,
            "token": token,
            "papel": papel,
            "expira_em": expira_em.isoformat(),
            "url": f"/convite/{token}",
        }

    def obter_convite(self, token: str) -> Dict[str, Any]:
        with db_cursor() as cursor:
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
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT id, obra_id, papel, expira_em, usado_em FROM convites WHERE token = %s",
                (token,),
            )
            convite = cursor.fetchone()
            if not convite:
                raise HTTPException(status_code=404, detail="Convite não encontrado")
            if convite["usado_em"]:
                raise HTTPException(status_code=400, detail="Este convite já foi utilizado")
            if convite["expira_em"] < datetime.utcnow():
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
                if convite["papel"] in PAPEIS_RATEIO:
                    rebalance_participacao(cursor, convite["obra_id"])
            cursor.execute(
                "UPDATE convites SET usado_em = %s WHERE id = %s",
                (datetime.utcnow(), convite["id"]),
            )
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

        with db_cursor() as cursor:
            cursor.execute(
                "SELECT papel FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
                (obra_id, membro_id),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Membro não encontrado")
            if row["papel"] == "owner":
                raise HTTPException(status_code=400, detail="Não é possível alterar o dono da obra")
            entrava = row["papel"] in PAPEIS_RATEIO
            entra = papel in PAPEIS_RATEIO
            cursor.execute(
                "UPDATE obra_membros SET papel = %s WHERE obra_id = %s AND usuario_id = %s",
                (papel, obra_id, membro_id),
            )
            if entrava != entra:
                rebalance_participacao(cursor, obra_id)
        return {"sucesso": True, "mensagem": "Papel atualizado"}

    def remover_membro(self, obra_id: int, owner_id: int, membro_id: int) -> Dict[str, Any]:
        assert_obra_access(obra_id, owner_id, "owner")
        if membro_id == owner_id:
            raise HTTPException(status_code=400, detail="Você não pode remover a si mesmo")

        with db_cursor() as cursor:
            cursor.execute(
                "SELECT papel FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
                (obra_id, membro_id),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Membro não encontrado")
            if row["papel"] == "owner":
                raise HTTPException(status_code=400, detail="Não é possível remover o dono da obra")
            entrava = row["papel"] in PAPEIS_RATEIO
            cursor.execute(
                "DELETE FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
                (obra_id, membro_id),
            )
            if entrava:
                rebalance_participacao(cursor, obra_id)
        return {"sucesso": True, "mensagem": "Membro removido da obra"}

    def definir_participacao(self, obra_id: int, owner_id: int, participantes: List[ParticipacaoItem]) -> Dict[str, Any]:
        assert_obra_access(obra_id, owner_id, "owner")
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT usuario_id, papel FROM obra_membros WHERE obra_id = %s",
                (obra_id,),
            )
            rows = cursor.fetchall()
            atuais = {row["usuario_id"] for row in rows if row["papel"] in PAPEIS_RATEIO}
            informados = [(item.usuario_id, item.percentual) for item in participantes]
            if {item[0] for item in informados} != atuais:
                raise HTTPException(status_code=400, detail="Informe o percentual de cada membro que entra no rateio")
            normalizados = validar_percentuais(informados)
            for usuario_id, percentual in normalizados:
                cursor.execute(
                    "UPDATE obra_membros SET participacao = %s WHERE obra_id = %s AND usuario_id = %s",
                    (percentual, obra_id, usuario_id),
                )
        return {"sucesso": True, "mensagem": "Participação atualizada"}

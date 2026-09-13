import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from database import db_cursor
from models import PendingActivity, Activity, PaidActivity, PaymentItem, ValorMembro
from utils.receipts import save_receipt


class ComprovantesManager:
    """Gerencia despesas de construção isoladas por obra."""

    def _parse_value(self, value_str: str) -> float:
        try:
            if isinstance(value_str, (int, float)):
                return float(value_str)

            clean_value = value_str.replace('R$', '').strip()
            if ',' in clean_value:
                clean_value = clean_value.replace('.', '').replace(',', '.')
            return float(clean_value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Formato de valor inválido: {value_str}")

    def _format_date(self, date_str: str) -> str:
        if not date_str:
            return None
        try:
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                year, month, day = date_str.split('-')
                return f"{day}/{month}/{year}"
            if re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                return date_str
            return date_str
        except Exception:
            return date_str

    def _pagamentos_map(self, cursor, atividade_ids: List[int]) -> Dict[int, List[PaymentItem]]:
        result: Dict[int, List[PaymentItem]] = {aid: [] for aid in atividade_ids}
        if not atividade_ids:
            return result
        placeholders = ",".join(["%s"] * len(atividade_ids))
        cursor.execute(
            f"""
            SELECT p.id, p.atividade_id, p.usuario_id, p.valor, p.comprovante_url, u.nome
            FROM pagamentos p
            JOIN usuarios u ON u.id = p.usuario_id
            WHERE p.atividade_id IN ({placeholders})
            ORDER BY p.id
            """,
            tuple(atividade_ids),
        )
        for row in cursor.fetchall():
            pagamento_id = row["id"]
            has_file = bool(row.get("comprovante_url"))
            result[row["atividade_id"]].append(
                PaymentItem(
                    id=pagamento_id,
                    usuario_id=row["usuario_id"],
                    nome=row["nome"],
                    valor=float(row["valor"] or 0),
                    comprovante_url=f"/pagamentos/{pagamento_id}/comprovante" if has_file else None,
                )
            )
        return result

    def _atualizar_status_atividade(self, cursor, atividade_id: int, valor_total: float):
        cursor.execute(
            "SELECT COALESCE(SUM(valor), 0) as total FROM pagamentos WHERE atividade_id = %s",
            (atividade_id,),
        )
        total_pago = float(cursor.fetchone()["total"] or 0)
        status = "paid" if total_pago >= float(valor_total) else "pending"
        cursor.execute(
            "UPDATE atividades SET status = %s WHERE idAtividades = %s",
            (status, atividade_id),
        )
        return total_pago, status

    def preencher_pagamento(
        self,
        valor_str: str,
        atividade_id: int,
        usuario_id: int,
        obra_id: int,
        data: Optional[str] = None,
        comprovante_bytes: Optional[bytes] = None,
        comprovante_ext: Optional[str] = None,
    ) -> Dict[str, Any]:
        valor = round(self._parse_value(valor_str), 2)
        if valor <= 0:
            raise HTTPException(status_code=400, detail="O valor do pagamento deve ser maior que zero")

        with db_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM obra_membros WHERE obra_id = %s AND usuario_id = %s",
                (obra_id, usuario_id),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="O pagador não é membro desta obra")

            cursor.execute(
                "SELECT * FROM atividades WHERE idAtividades = %s AND obra_id = %s",
                (atividade_id, obra_id),
            )
            activity = cursor.fetchone()
            if not activity:
                raise HTTPException(status_code=404, detail="Atividade não encontrada")

            cursor.execute(
                "SELECT COALESCE(SUM(valor), 0) as total FROM pagamentos WHERE atividade_id = %s",
                (atividade_id,),
            )
            total_pago = round(float(cursor.fetchone()["total"] or 0), 2)
            restante = round(float(activity["valor"]) - total_pago, 2)
            if valor > restante:
                raise HTTPException(
                    status_code=400,
                    detail=f"O valor excede o restante da atividade (R$ {restante:.2f})",
                )

            data_formatada = self._format_date(data) if data else activity.get("data")
            cursor.execute(
                "INSERT INTO pagamentos (atividade_id, usuario_id, valor, data) VALUES (%s, %s, %s, %s)",
                (activity["idAtividades"], usuario_id, valor, data_formatada),
            )
            pagamento_id = cursor.lastrowid
            comprovante_url = None
            if comprovante_bytes and comprovante_ext:
                relative = save_receipt(obra_id, comprovante_bytes, comprovante_ext)
                cursor.execute(
                    "UPDATE pagamentos SET comprovante_url = %s WHERE id = %s",
                    (relative, pagamento_id),
                )
                comprovante_url = f"/pagamentos/{pagamento_id}/comprovante"
            self._atualizar_status_atividade(cursor, activity["idAtividades"], activity["valor"])
            return {
                "sucesso": True,
                "mensagem": f"Pagamento no valor de R$ {valor:.2f} registrado na atividade '{activity['nome']}'",
                "data": data_formatada,
                "pagamento_id": pagamento_id,
                "comprovante_url": comprovante_url,
            }

    def obter_comprovante(self, pagamento_id: int, obra_id: int) -> str:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT p.comprovante_url
                FROM pagamentos p
                JOIN atividades a ON a.idAtividades = p.atividade_id
                WHERE p.id = %s AND a.obra_id = %s
                """,
                (pagamento_id, obra_id),
            )
            row = cursor.fetchone()
        if not row or not row.get("comprovante_url"):
            raise HTTPException(status_code=404, detail="Comprovante não encontrado")
        return row["comprovante_url"]

    def atualizar_status(self, obra_id: int) -> Dict[str, Any]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                UPDATE atividades a
                SET status = CASE
                    WHEN COALESCE((SELECT SUM(p.valor) FROM pagamentos p WHERE p.atividade_id = a.idAtividades), 0) >= a.valor
                    THEN 'paid' ELSE 'pending'
                END
                WHERE a.obra_id = %s
                """,
                (obra_id,),
            )
            updated_count = cursor.rowcount
        return {
            "sucesso": True,
            "mensagem": "Status do pagamento atualizado com sucesso",
            "atividades_atualizadas": updated_count,
        }

    def _listar_base(self, obra_id: int, extra_where: str = "", having: str = ""):
        with db_cursor() as cursor:
            query = f"""
                SELECT a.idAtividades, a.nome, a.setor, a.valor, a.data, a.status,
                       COALESCE(SUM(p.valor), 0) as total_pago
                FROM atividades a
                LEFT JOIN pagamentos p ON p.atividade_id = a.idAtividades
                WHERE a.obra_id = %s {extra_where}
                GROUP BY a.idAtividades, a.nome, a.setor, a.valor, a.data, a.status
                {having}
            """
            cursor.execute(query, (obra_id,))
            rows = cursor.fetchall()
            pagamentos = self._pagamentos_map(cursor, [r["idAtividades"] for r in rows])
        return rows, pagamentos

    def listar_atividades_pendentes(self, obra_id: int) -> List[PendingActivity]:
        rows, pagamentos = self._listar_base(
            obra_id,
            extra_where="AND a.status = 'pending'",
            having="HAVING (a.valor - COALESCE(SUM(p.valor), 0)) > 0",
        )
        result = []
        for activity in rows:
            total_pago = float(activity["total_pago"] or 0)
            result.append(PendingActivity(
                id=activity["idAtividades"],
                activity=activity["nome"],
                sector=activity["setor"],
                total_value=float(activity["valor"]),
                valor_restante=float(activity["valor"]) - total_pago,
                date=activity["data"],
                total_pago=total_pago,
                pagamentos=pagamentos.get(activity["idAtividades"], []),
            ))
        return result

    def listar_atividades(self, obra_id: int) -> List[Activity]:
        rows, pagamentos = self._listar_base(obra_id)
        result = []
        for activity in rows:
            total_pago = float(activity["total_pago"] or 0)
            valor = float(activity["valor"])
            result.append(Activity(
                id=activity["idAtividades"],
                activity=activity["nome"],
                sector=activity["setor"],
                value=valor,
                date=activity["data"],
                total_pago=total_pago,
                valor_restante=valor - total_pago,
                pagamentos=pagamentos.get(activity["idAtividades"], []),
                status=activity["status"],
            ))
        return result

    def listar_atividades_pagas(self, obra_id: int) -> List[PaidActivity]:
        rows, pagamentos = self._listar_base(obra_id, extra_where="AND a.status = 'paid'")
        result = []
        for activity in rows:
            total_pago = float(activity["total_pago"] or 0)
            result.append(PaidActivity(
                id=activity["idAtividades"],
                activity=activity["nome"],
                sector=activity["setor"],
                total_value=float(activity["valor"]),
                date=activity["data"],
                total_pago=total_pago,
                pagamentos=pagamentos.get(activity["idAtividades"], []),
                status=activity["status"],
            ))
        return result

    def adicionar_atividade(self, data: str, valor: float, setor: str, atividade: str, obra_id: int) -> Dict[str, Any]:
        if not atividade or not setor:
            raise HTTPException(status_code=400, detail="Atividade e setor são obrigatórios")
        if valor <= 0:
            raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")

        data_formatada = self._format_date(data)
        with db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO atividades (obra_id, nome, valor, data, setor, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (obra_id, atividade, valor, data_formatada, setor, "pending"),
            )
            activity_id = cursor.lastrowid
        return {
            "sucesso": True,
            "mensagem": f"Atividade '{atividade}' adicionada com sucesso",
            "id": activity_id,
        }

    def excluir_atividade(self, id: int, obra_id: int) -> Dict[str, Any]:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT nome FROM atividades WHERE idAtividades = %s AND obra_id = %s",
                (id, obra_id),
            )
            activity = cursor.fetchone()
            if not activity:
                raise HTTPException(status_code=404, detail=f"Atividade com ID {id} não encontrada")
            cursor.execute("DELETE FROM atividades WHERE idAtividades = %s AND obra_id = %s", (id, obra_id))
        return {"sucesso": True, "mensagem": f"Atividade '{activity['nome']}' excluída com sucesso"}

    def editar_atividade(
        self,
        id: int,
        obra_id: int,
        atividade: Optional[str] = None,
        setor: Optional[str] = None,
        valor: Optional[float] = None,
        data: Optional[str] = None,
    ) -> Dict[str, Any]:
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM atividades WHERE idAtividades = %s AND obra_id = %s",
                (id, obra_id),
            )
            activity = cursor.fetchone()
            if not activity:
                raise HTTPException(status_code=404, detail=f"Atividade com ID {id} não encontrada")

            update_fields = []
            params = []
            if atividade is not None:
                update_fields.append("nome = %s")
                params.append(atividade)
            if setor is not None:
                update_fields.append("setor = %s")
                params.append(setor)
            if valor is not None:
                if valor <= 0:
                    raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
                update_fields.append("valor = %s")
                params.append(valor)
            if data is not None:
                update_fields.append("data = %s")
                params.append(self._format_date(data))

            new_total = valor if valor is not None else activity["valor"]
            if update_fields:
                params.append(id)
                params.append(obra_id)
                cursor.execute(
                    "UPDATE atividades SET " + ", ".join(update_fields) + " WHERE idAtividades = %s AND obra_id = %s",
                    params,
                )

            _, status = self._atualizar_status_atividade(cursor, id, new_total)
        return {
            "sucesso": True,
            "mensagem": f"Atividade ID {id} atualizada com sucesso",
            "status_atual": status,
        }

    def calcular_valor_total(self, obra_id: int) -> float:
        with db_cursor() as cursor:
            cursor.execute("SELECT SUM(valor) as total FROM atividades WHERE obra_id = %s", (obra_id,))
            result = cursor.fetchone()
        return (result["total"] if result else 0) or 0

    def calcular_valor_total_pago(self, obra_id: int) -> float:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(p.valor), 0) as total
                FROM pagamentos p
                JOIN atividades a ON a.idAtividades = p.atividade_id
                WHERE a.obra_id = %s
                """,
                (obra_id,),
            )
            result = cursor.fetchone()
        return (result["total"] if result else 0) or 0

    def calcular_valor_pago_membros(self, obra_id: int) -> List[ValorMembro]:
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id as usuario_id, u.nome, COALESCE(pay.total, 0) as total
                FROM obra_membros om
                JOIN usuarios u ON u.id = om.usuario_id
                LEFT JOIN (
                    SELECT p.usuario_id, SUM(p.valor) as total
                    FROM pagamentos p
                    JOIN atividades a ON a.idAtividades = p.atividade_id
                    WHERE a.obra_id = %s
                    GROUP BY p.usuario_id
                ) pay ON pay.usuario_id = u.id
                WHERE om.obra_id = %s
                GROUP BY u.id, u.nome, pay.total
                ORDER BY total DESC, u.nome
                """,
                (obra_id, obra_id),
            )
            rows = cursor.fetchall()
        return [
            ValorMembro(usuario_id=row["usuario_id"], nome=row["nome"], total=float(row["total"] or 0))
            for row in rows
        ]

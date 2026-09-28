import json
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from database import DISPLAY_NAME_SQL, db_cursor
from models import (
    PendingActivity, Activity, PaidActivity, PaymentItem, ValorMembro,
    SaldoMembro, ResumoObra, ParticipacaoAtividade, Transferencia,
)
from utils.receipts import save_receipt


def centavos(value) -> int:
    quantized = Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def percentuais_iguais(quantidade: int) -> List[float]:
    if quantidade <= 0:
        return []
    base, rem = divmod(10000, quantidade)
    return [(base + (1 if index < rem else 0)) / 100.0 for index in range(quantidade)]


def partes_em_centavos(total_centavos: int, percentuais: List[float]) -> List[int]:
    pesos = [centavos(percentual) for percentual in percentuais]
    total_pesos = sum(pesos)
    if total_centavos <= 0 or total_pesos <= 0:
        return [0] * len(percentuais)
    base = [total_centavos * peso // total_pesos for peso in pesos]
    resto = total_centavos - sum(base)
    for index in range(resto):
        base[index] += 1
    return base


def validar_percentuais(itens: List[Tuple[int, Any]]) -> List[Tuple[int, float]]:
    if not itens:
        raise HTTPException(status_code=400, detail="Informe a participação")
    ids = [int(item[0]) for item in itens]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Participação duplicada")
    normalizados = []
    soma = 0
    for usuario_id, percentual in itens:
        pontos = centavos(percentual)
        if pontos <= 0:
            raise HTTPException(status_code=400, detail="Cada percentual deve ser maior que zero")
        soma += pontos
        normalizados.append((int(usuario_id), pontos / 100.0))
    if soma != 10000:
        raise HTTPException(status_code=400, detail="A soma da participação deve ser 100%")
    normalizados.sort(key=lambda item: item[0])
    return normalizados


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
            SELECT p.id, p.atividade_id, p.usuario_id, p.valor, p.comprovante_url, {DISPLAY_NAME_SQL} as nome
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

    def _participacoes_map(self, cursor, atividade_ids: List[int]) -> Dict[int, List[ParticipacaoAtividade]]:
        result: Dict[int, List[ParticipacaoAtividade]] = {aid: [] for aid in atividade_ids}
        if not atividade_ids:
            return result
        placeholders = ",".join(["%s"] * len(atividade_ids))
        cursor.execute(
            f"""
            SELECT ap.atividade_id, ap.usuario_id, ap.percentual, {DISPLAY_NAME_SQL} as nome
            FROM atividade_participacoes ap
            JOIN usuarios u ON u.id = ap.usuario_id
            WHERE ap.atividade_id IN ({placeholders})
            ORDER BY ap.usuario_id
            """,
            tuple(atividade_ids),
        )
        for row in cursor.fetchall():
            result[row["atividade_id"]].append(
                ParticipacaoAtividade(
                    usuario_id=row["usuario_id"],
                    nome=row["nome"],
                    percentual=float(row["percentual"]),
                )
            )
        return result

    def _participacao_vigente(self, cursor, obra_id: int) -> List[Tuple[int, float]]:
        cursor.execute(
            """
            SELECT usuario_id, participacao
            FROM obra_membros
            WHERE obra_id = %s AND papel <> 'leitura' AND participacao IS NOT NULL
            ORDER BY usuario_id
            """,
            (obra_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=400, detail="Nenhum membro entra no rateio desta obra")
        return validar_percentuais([(row["usuario_id"], row["participacao"]) for row in rows])

    def _parse_participacao_custom(self, cursor, raw: str) -> List[Tuple[int, float]]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Participação inválida")
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="Participação inválida")
        itens = []
        for item in data:
            if not isinstance(item, dict) or "usuario_id" not in item or "percentual" not in item:
                raise HTTPException(status_code=400, detail="Participação inválida")
            try:
                itens.append((int(item["usuario_id"]), item["percentual"]))
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Participação inválida")
        normalizados = validar_percentuais(itens)
        ids = [item[0] for item in normalizados]
        placeholders = ",".join(["%s"] * len(ids))
        cursor.execute(f"SELECT id FROM usuarios WHERE id IN ({placeholders})", tuple(ids))
        found = {row["id"] for row in cursor.fetchall()}
        if len(found) != len(ids):
            raise HTTPException(status_code=400, detail="Participação com usuário inválido")
        return normalizados

    def _substituir_participacao(self, cursor, atividade_id: int, shares: List[Tuple[int, float]]):
        cursor.execute("DELETE FROM atividade_participacoes WHERE atividade_id = %s", (atividade_id,))
        for usuario_id, percentual in shares:
            cursor.execute(
                """
                INSERT INTO atividade_participacoes (atividade_id, usuario_id, percentual)
                VALUES (%s, %s, %s)
                """,
                (atividade_id, usuario_id, percentual),
            )

    def _aplicar_participacao(self, cursor, obra_id: int, atividade_id: int, raw: Optional[str], criar: bool):
        texto = (raw or "").strip()
        if not texto:
            if not criar:
                return
            shares = self._participacao_vigente(cursor, obra_id)
        elif texto == "obra":
            shares = self._participacao_vigente(cursor, obra_id)
        else:
            shares = self._parse_participacao_custom(cursor, texto)
        self._substituir_participacao(cursor, atividade_id, shares)

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
        with db_cursor() as cursor:
            participacoes = self._participacoes_map(cursor, [row["idAtividades"] for row in rows])
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
                participacao=participacoes.get(activity["idAtividades"], []),
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

    def adicionar_atividade(
        self,
        data: str,
        valor: float,
        setor: str,
        atividade: str,
        obra_id: int,
        participacao: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            self._aplicar_participacao(cursor, obra_id, activity_id, participacao, criar=True)
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
        participacao: Optional[str] = None,
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
            self._aplicar_participacao(cursor, obra_id, id, participacao, criar=False)
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
                f"""
                SELECT u.id as usuario_id, {DISPLAY_NAME_SQL} as nome, COALESCE(pay.total, 0) as total
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
                GROUP BY u.id, u.nome, u.nome_exibicao, pay.total
                ORDER BY total DESC, nome
                """,
                (obra_id, obra_id),
            )
            rows = cursor.fetchall()
        return [
            ValorMembro(usuario_id=row["usuario_id"], nome=row["nome"], total=float(row["total"] or 0))
            for row in rows
        ]

    def _transferencias(self, saldos: List[SaldoMembro]) -> List[Transferencia]:
        devedores = []
        credores = []
        for item in saldos:
            pontos = centavos(item.saldo)
            if pontos > 0:
                devedores.append([item.usuario_id, item.nome, pontos])
            elif pontos < 0:
                credores.append([item.usuario_id, item.nome, -pontos])
        devedores.sort(key=lambda row: (-row[2], row[0]))
        credores.sort(key=lambda row: (-row[2], row[0]))
        i = 0
        j = 0
        resultado = []
        while i < len(devedores) and j < len(credores):
            valor = min(devedores[i][2], credores[j][2])
            if valor > 0:
                resultado.append(Transferencia(
                    de_usuario_id=devedores[i][0],
                    de_nome=devedores[i][1],
                    para_usuario_id=credores[j][0],
                    para_nome=credores[j][1],
                    valor=valor / 100.0,
                ))
            devedores[i][2] -= valor
            credores[j][2] -= valor
            if devedores[i][2] == 0:
                i += 1
            if credores[j][2] == 0:
                j += 1
        return resultado

    def calcular_acerto(self, obra_id: int):
        with db_cursor() as cursor:
            cursor.execute(
                """
                SELECT a.idAtividades, COALESCE(SUM(p.valor), 0) as total_pago
                FROM atividades a
                LEFT JOIN pagamentos p ON p.atividade_id = a.idAtividades
                WHERE a.obra_id = %s
                GROUP BY a.idAtividades
                """,
                (obra_id,),
            )
            atividades = cursor.fetchall()
            ids = [row["idAtividades"] for row in atividades]
            participacoes = self._participacoes_map(cursor, ids)
            pagamentos = self._pagamentos_map(cursor, ids)
            cursor.execute(
                f"""
                SELECT om.usuario_id, {DISPLAY_NAME_SQL} as nome
                FROM obra_membros om
                JOIN usuarios u ON u.id = om.usuario_id
                WHERE om.obra_id = %s AND om.papel <> 'leitura'
                """,
                (obra_id,),
            )
            atuais = cursor.fetchall()

        parte: Dict[int, int] = {}
        pago: Dict[int, int] = {}
        nomes: Dict[int, str] = {}
        for row in atividades:
            atividade_id = row["idAtividades"]
            shares = participacoes.get(atividade_id, [])
            total_pago_cents = centavos(row["total_pago"])
            if shares:
                fatias = partes_em_centavos(total_pago_cents, [item.percentual for item in shares])
                for item, fatia in zip(shares, fatias):
                    parte[item.usuario_id] = parte.get(item.usuario_id, 0) + fatia
                    nomes[item.usuario_id] = item.nome
            for pagamento in pagamentos.get(atividade_id, []):
                pago[pagamento.usuario_id] = pago.get(pagamento.usuario_id, 0) + centavos(pagamento.valor)
                nomes[pagamento.usuario_id] = pagamento.nome

        for membro in atuais:
            parte.setdefault(membro["usuario_id"], 0)
            pago.setdefault(membro["usuario_id"], 0)
            nomes[membro["usuario_id"]] = membro["nome"]

        saldos = []
        for usuario_id, nome in nomes.items():
            parte_cents = parte.get(usuario_id, 0)
            pago_cents = pago.get(usuario_id, 0)
            saldos.append(SaldoMembro(
                usuario_id=usuario_id,
                nome=nome,
                pago=pago_cents / 100.0,
                parte=parte_cents / 100.0,
                saldo=(parte_cents - pago_cents) / 100.0,
            ))
        saldos.sort(key=lambda item: (-item.saldo, item.nome))
        return saldos, self._transferencias(saldos)

    def montar_resumo(self, obra_id: int) -> ResumoObra:
        atividades = self.listar_atividades(obra_id)
        total = float(self.calcular_valor_total(obra_id) or 0)
        total_pago = float(self.calcular_valor_total_pago(obra_id) or 0)
        membros = self.calcular_valor_pago_membros(obra_id)
        saldos, transferencias = self.calcular_acerto(obra_id)
        return ResumoObra(
            total=round(total, 2),
            total_pago=round(total_pago, 2),
            restante=round(total - total_pago, 2),
            membros=membros,
            saldos=saldos,
            transferencias=transferencias,
            atividades=atividades,
        )

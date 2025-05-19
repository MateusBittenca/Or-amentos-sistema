import re
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from config import logger
from database import get_db_connection
from models import PendingActivity, Activity

class ComprovantesManager:
    """Classe para gerenciar despesas de construção no banco de dados MySQL"""
    
    def __init__(self):
        # Isso estará vazio, pois usaremos conexões DB conforme necessário
        pass
    
    def _parse_value(self, value_str: str) -> float:
        """Converter valor string para float, lidando com diferentes formatos"""
        try:
            # Log para diagnóstico
            logger.debug(f"Analisando valor: '{value_str}', tipo: {type(value_str)}")
            
            if isinstance(value_str, (int, float)):
                return float(value_str)
                    
            # Remover símbolos de moeda e espaços
            clean_value = value_str.replace('R$', '').strip()
            logger.debug(f"Valor limpo após remover símbolo de moeda: '{clean_value}'")
            
            # Substituir separadores - formato brasileiro (1.234,56) para ponto decimal (1234.56)
            if ',' in clean_value:
                # Se tiver vírgula, assume formato brasileiro
                clean_value = clean_value.replace('.', '').replace(',', '.')
            
            logger.debug(f"Valor limpo final: '{clean_value}'")
            
            return float(clean_value)
        except ValueError as e:
            logger.error(f"Erro de análise de valor para '{value_str}': {str(e)}")
            raise HTTPException(status_code=400, detail=f"Formato de valor inválido: {value_str}")
    
    def _format_date(self, date_str: str) -> str:
        """Formatar data para formato de exibição (DD/MM/AAAA)"""
        if not date_str:
            return None
            
        try:
            # Verificar se o formato é AAAA-MM-DD (do input HTML type="date")
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                # Converter para DD/MM/AAAA para armazenamento
                year, month, day = date_str.split('-')
                return f"{day}/{month}/{year}"
            elif re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                # Já está no formato DD/MM/AAAA
                return date_str
            else:
                logger.warning(f"Formato de data desconhecido: {date_str}")
                return date_str  # Retornar como está se o formato for desconhecido
        except Exception as e:
            logger.error(f"Erro ao formatar data {date_str}: {e}")
            return date_str  # Retornar como está se houver um erro
    
    def preencher_pagamento(self, valor_str: str, atividade: str, pagador: str, 
                            setor: Optional[str] = None, data: Optional[str] = None) -> Dict[str, Any]:
        """Registrar um pagamento no banco de dados"""
        # Converter valor para float
        valor = self._parse_value(valor_str)
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Encontrar atividade correspondente
            query = "SELECT * FROM atividades WHERE nome = %s"
            params = (atividade,)
            
            if setor:
                query += " AND setor = %s"
                params = (atividade, setor)
                
            cursor.execute(query, params)
            activity = cursor.fetchone()
            
            if not activity:
                cursor.close()
                connection.close()
                raise HTTPException(status_code=404, detail=f"Atividade '{atividade}' não encontrada")
            
            # Determinar qual campo atualizar com base no pagador
            field_to_update = ""
            if pagador.lower() in ['alex-rute', 'alex rute', 'alex', 'rute']:
                field_to_update = "alex_rute"
                new_value = (activity['alex_rute'] or 0) + valor
            elif pagador.lower() in ['diego-ana', 'diego ana', 'diego', 'ana']:
                field_to_update = "diego_ana"
                new_value = (activity['diego_ana'] or 0) + valor
            else:
                # Tentar inferir com base no nome extraído do comprovante
                if 'alex' in pagador.lower() or 'rute' in pagador.lower():
                    field_to_update = "alex_rute"
                    new_value = (activity['alex_rute'] or 0) + valor
                elif 'diego' in pagador.lower() or 'ana' in pagador.lower():
                    field_to_update = "diego_ana"
                    new_value = (activity['diego_ana'] or 0) + valor
                else:
                    cursor.close()
                    connection.close()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Pagador '{pagador}' não reconhecido. Use 'Alex-Rute' ou 'Diego-Ana'"
                    )
            
            # Atualizar o campo
            update_query = f"UPDATE atividades SET {field_to_update} = %s WHERE idAtividades = %s"
            cursor.execute(update_query, (new_value, activity['idAtividades']))
            
            # Atualizar status de pagamento
            total_paid = (activity['alex_rute'] or 0) + (activity['diego_ana'] or 0) + valor
            status = "paid" if total_paid >= activity['valor'] else "pending"
            
            cursor.execute("UPDATE atividades SET status = %s WHERE idAtividades = %s", 
                          (status, activity['idAtividades']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "sucesso": True,
                "mensagem": f"Pagamento no valor de R$ {valor:.2f} Registrado na atividade : '{atividade}' por {pagador}",
                "data": data
            }
        except HTTPException as he:
            # Relançar exceções HTTP
            raise he
        except Exception as e:
            logger.error(f"Erro ao registrar pagamento: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao registrar pagamento: {str(e)}")
            
    def atualizar_status(self) -> Dict[str, Any]:
        """Atualizar status de pagamento para todas as atividades com base nos valores preenchidos"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Obter todas as atividades
            cursor.execute("SELECT * FROM atividades")
            activities = cursor.fetchall()
            
            updated_count = 0
            
            for activity in activities:
                value = activity['valor'] or 0
                alex_rute = activity['alex_rute'] or 0
                diego_ana = activity['diego_ana'] or 0
                
                # Calcular status
                status = "paid" if (alex_rute + diego_ana) >= value else "pending"
                
                # Atualizar status
                cursor.execute("UPDATE atividades SET status = %s WHERE idAtividades = %s",
                               (status, activity['idAtividades']))
                updated_count += 1
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "sucesso": True,
                "mensagem": "Status do pagamento atualizado com sucesso",
                "atividades_atualizadas": updated_count
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")
    
    def listar_atividades_pendentes(self) -> List[PendingActivity]:
        """Listar todas as atividades com pagamentos pendentes"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM atividades WHERE status = 'pending'")
            activities = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            atividades_pendentes = []
            
            for activity in activities:
                valor_custo = activity['valor'] or 0
                alex_rute = activity['alex_rute'] or 0
                diego_ana = activity['diego_ana'] or 0
                
                # Calcular valor restante a ser pago
                valor_restante = valor_custo - (alex_rute + diego_ana)
                
                # Obter string de data diretamente do banco de dados
                date_str = activity['data']
                
                # Verificar se ainda há valor pendente
                if valor_restante > 0:
                    atividades_pendentes.append(PendingActivity(
                        id=activity['idAtividades'],
                        activity=activity['nome'],
                        sector=activity['setor'],
                        total_value=valor_custo,
                        valor_restante=valor_restante,
                        date=date_str,
                        alex_rute=alex_rute,
                        diego_ana=diego_ana
                    ))
                    
            return atividades_pendentes
        except Exception as e:
            logger.error(f"Erro ao listar atividades pendentes: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar atividades pendentes: {str(e)}")
    
    def listar_atividades(self) -> List[Activity]:
        """Listar todas as atividades no banco de dados"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM atividades")
            db_activities = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            activities_list = []
            
            for activity in db_activities:
                # Data já está armazenada como string
                date_str = activity['data']
                    
                activities_list.append(Activity(
                    id=activity['idAtividades'],
                    activity=activity['nome'],
                    sector=activity['setor'],
                    value=activity['valor'],
                    date=date_str,
                    diego_ana=activity['diego_ana'] or 0,
                    alex_rute=activity['alex_rute'] or 0
                ))
            
            return activities_list
        except Exception as e:
            logger.error(f"Erro ao listar atividades: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar atividades: {str(e)}")
    
    def adicionar_atividade(self, data: str, valor: float, 
                           setor: str, atividade: str) -> Dict[str, Any]:
        """Adicionar uma nova atividade ao banco de dados"""
        try:
            logger.debug(f"Adicionando atividade: data={data}, valor={valor}, setor={setor}, atividade={atividade}")
            
            # Formatar string de data para armazenamento
            date_str = self._format_date(data) if data else None
            
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Inserir nova atividade
            query = """
            INSERT INTO atividades (nome, setor, valor, data, alex_rute, diego_ana, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (atividade, setor, float(valor), date_str, 0, 0, "pending"))
            
            # Obter o ID da linha inserida
            activity_id = cursor.lastrowid
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "mensagem": f"Atividade: '{atividade}' adicionada com sucesso",
                "id": activity_id,
                "atividade": atividade,
                "setor": setor,
                "valor": float(valor),
                "data": date_str
            }
        except HTTPException as he:
            # Relançar exceções HTTP
            raise he
        except Exception as e:
            logger.error(f"Erro inesperado ao adicionar a atividade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao adcionar a atividade: {str(e)}")
        
    def excluir_atividade(self, id: int) -> Dict[str, Any]:
        """Excluir uma atividade pelo seu ID"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Verificar se a atividade existe
            cursor.execute("SELECT nome FROM atividades WHERE idAtividades = %s", (id,))
            activity = cursor.fetchone()
            
            if not activity:
                cursor.close()
                connection.close()
                raise HTTPException(status_code=404, detail="Atividade não encontrada")
            
            # Excluir atividade
            cursor.execute("DELETE FROM atividades WHERE idAtividades = %s", (id,))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "message": f"Atividade: '{activity['nome']}' removida com sucesso!"
            }
        except HTTPException as he:
            # Relançar exceções HTTP
            raise he
        except Exception as e:
            logger.error(f"Erro ao excluir atividade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao excluir atividade: {str(e)}")
            
    def calcular_valor_total(self) -> float:
        """Calcular valor total da construção somando os valores das atividades"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(valor) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Erro ao calcular valor total: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular valor total: {str(e)}")
    
    def calcular_valor_total_pago(self) -> float:
        """Calcular valor total pago somando valores nas colunas Alex-Rute e Diego-Ana"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(alex_rute) + SUM(diego_ana) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Erro ao calcular total pago: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular total pago: {str(e)}")
    
    def calcular_valor_pago_diego(self) -> float:
        """Calcular valor total pago por Diego-Ana"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(diego_ana) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Erro ao calcular total pago por Diego-Ana: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular total pago por Diego-Ana: {str(e)}")

    def calcular_valor_pago_alex(self) -> float:
        """Calcular valor total pago por Alex-Rute"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(alex_rute) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Erro ao calcular total pago por Alex-Rute: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular total pago por Alex-Rute: {str(e)}")
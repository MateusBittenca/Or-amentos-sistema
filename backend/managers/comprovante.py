import re
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from config import logger
from database import get_db_connection
from models import PendingActivity, Activity, PaidActivity
from utils.cache import cached, clear_cache

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
            
            # Calcular novo status no mesmo passo
            total_paid = 0
            if field_to_update == "alex_rute":
                total_paid = new_value + (activity['diego_ana'] or 0)
            else:
                total_paid = (activity['alex_rute'] or 0) + new_value
                
            status = "paid" if total_paid >= activity['valor'] else "pending"
            
            # Atualizar o campo e status em uma única operação
            update_query = f"UPDATE atividades SET {field_to_update} = %s, status = %s WHERE idAtividades = %s"
            cursor.execute(update_query, (new_value, status, activity['idAtividades']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Limpar o cache após alterar os dados
            clear_cache("activities")
            
            return {
                "sucesso": True,
                "mensagem": f"Pagamento no valor de R$ {valor:.2f} Registrado na atividade : '{atividade}' por {pagador}",
                "data": data
            }
        except HTTPException as he:
            # Relançar exceções HTTP
            raise he
        except Exception as e:
            logger.error(f"Erro ao registrar pagamento: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao registrar pagamento: {str(e)}")
                
    def atualizar_status(self) -> Dict[str, Any]:
        """Atualizar status de pagamento para todas as atividades com base nos valores preenchidos"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Atualizar status em uma única operação SQL para melhor performance
            update_query = """
                UPDATE atividades 
                SET status = CASE 
                    WHEN (COALESCE(alex_rute, 0) + COALESCE(diego_ana, 0)) >= valor THEN 'paid' 
                    ELSE 'pending' 
                END
            """
            cursor.execute(update_query)
            updated_count = cursor.rowcount
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Limpar cache após atualização
            clear_cache("activities")
            
            return {
                "sucesso": True,
                "mensagem": "Status do pagamento atualizado com sucesso",
                "atividades_atualizadas": updated_count
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")
    
    @cached(expiry=30, key_prefix="activities")
    def listar_atividades_pendentes(self) -> List[PendingActivity]:
        """Listar todas as atividades com pagamentos pendentes"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Otimizar a consulta para retornar apenas atividades pendentes em uma única operação
            query = """
                SELECT idAtividades, nome, setor, valor, data, 
                       COALESCE(alex_rute, 0) as alex_rute, 
                       COALESCE(diego_ana, 0) as diego_ana,
                       (valor - COALESCE(alex_rute, 0) - COALESCE(diego_ana, 0)) as valor_restante
                FROM atividades 
                WHERE status = 'pending' AND 
                      (valor - COALESCE(alex_rute, 0) - COALESCE(diego_ana, 0)) > 0
            """
            cursor.execute(query)
            activities = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            atividades_pendentes = []
            
            for activity in activities:
                atividades_pendentes.append(PendingActivity(
                    id=activity['idAtividades'],
                    activity=activity['nome'],
                    sector=activity['setor'],
                    total_value=activity['valor'],
                    valor_restante=activity['valor_restante'],
                    date=activity['data'],
                    alex_rute=activity['alex_rute'],
                    diego_ana=activity['diego_ana']
                ))
                    
            return atividades_pendentes
        except Exception as e:
            logger.error(f"Erro ao listar atividades pendentes: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar atividades pendentes: {str(e)}")
    
    @cached(expiry=30, key_prefix="activities") 
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
                    alex_rute=activity['alex_rute'] or 0,
                    status=activity['status']
                ))
            
            return activities_list
        except Exception as e:
            logger.error(f"Erro ao listar atividades: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar atividades: {str(e)}")
    
    @cached(expiry=30, key_prefix="activities")    
    def listar_atividades_pagas(self) -> List[PaidActivity]:
        """Listar todas as atividades pagas"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM atividades WHERE status = 'paid'")
            db_activities = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            atividades_pagas = []
            
            for activity in db_activities:
                # Data já está armazenada como string
                date_str = activity['data']
                    
                atividades_pagas.append(PaidActivity(
                    id=activity['idAtividades'],
                    activity=activity['nome'],
                    sector=activity['setor'],
                    total_value=activity['valor'],
                    date=date_str,
                    diego_ana=activity['diego_ana'] or 0,
                    alex_rute=activity['alex_rute'] or 0,
                    status=activity['status']
                ))
            
            return atividades_pagas
        except Exception as e:
            logger.error(f"Erro ao listar atividades pagas: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar atividades pagas: {str(e)}")
            
    def adicionar_atividade(self, data: str, valor: float, 
                           setor: str, atividade: str) -> Dict[str, Any]:
        """Adicionar uma nova atividade ao banco de dados"""
        try:
            logger.debug(f"Adicionando atividade: {atividade}, setor: {setor}, valor: {valor}, data: {data}")
            
            # Verificar valores
            if not atividade or not setor:
                raise HTTPException(status_code=400, detail="Atividade e setor são obrigatórios")
                
            if valor <= 0:
                raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
                
            # Formatar data
            data_formatada = self._format_date(data)
            
            # Inserir atividade
            connection = get_db_connection()
            cursor = connection.cursor()
            
            insert_query = """
                INSERT INTO atividades (nome, valor, data, setor, status) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (atividade, valor, data_formatada, setor, "pending"))
            
            activity_id = cursor.lastrowid
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Limpar cache após adicionar
            clear_cache("activities")
            
            return {
                "sucesso": True, 
                "mensagem": f"Atividade '{atividade}' adicionada com sucesso",
                "id": activity_id
            }
        except HTTPException as he:
            # Relançar exceções HTTP
            raise he
        except Exception as e:
            logger.error(f"Erro ao adicionar atividade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao adicionar atividade: {str(e)}")
    
    def excluir_atividade(self, id: int) -> Dict[str, Any]:
        """Excluir uma atividade pelo ID"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Verificar se a atividade existe
            cursor.execute("SELECT nome FROM atividades WHERE idAtividades = %s", (id,))
            activity = cursor.fetchone()
            
            if not activity:
                cursor.close()
                connection.close()
                raise HTTPException(status_code=404, detail=f"Atividade com ID {id} não encontrada")
            
            activity_name = activity['nome']
                
            # Excluir a atividade
            cursor.execute("DELETE FROM atividades WHERE idAtividades = %s", (id,))
            connection.commit()
            
            cursor.close()
            connection.close()
            
            # Limpar cache após excluir
            clear_cache("activities")
            
            return {
                "sucesso": True,
                "mensagem": f"Atividade '{activity_name}' excluída com sucesso"
            }
        except HTTPException as he:
            # Relançar exceções HTTP
            raise he
        except Exception as e:
            logger.error(f"Erro ao excluir atividade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao excluir atividade: {str(e)}")
    
    @cached(expiry=30, key_prefix="valor_total")
    def calcular_valor_total(self) -> float:
        """Calcular o valor total das atividades"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Usar SQL para calcular a soma diretamente
            cursor.execute("SELECT SUM(valor) as total FROM atividades")
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            # Retornar o valor total ou 0 se for NULL
            return result[0] or 0
        except Exception as e:
            logger.error(f"Erro ao calcular valor total: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular valor total: {str(e)}")
    
    @cached(expiry=30, key_prefix="valor_total_pago")
    def calcular_valor_total_pago(self) -> float:
        """Calcular o valor total pago"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Usar SQL para calcular a soma diretamente
            cursor.execute("SELECT SUM(COALESCE(alex_rute, 0) + COALESCE(diego_ana, 0)) as total_pago FROM atividades")
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            # Retornar o valor total pago ou 0 se for NULL
            return result[0] or 0
        except Exception as e:
            logger.error(f"Erro ao calcular valor total pago: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular valor total pago: {str(e)}")
    
    @cached(expiry=30, key_prefix="valor_pago_diego")
    def calcular_valor_pago_diego(self) -> float:
        """Calcular o valor total pago por Diego-Ana"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Usar SQL para calcular a soma diretamente
            cursor.execute("SELECT SUM(COALESCE(diego_ana, 0)) as total_diego FROM atividades")
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            # Retornar o valor total pago por Diego-Ana ou 0 se for NULL
            return result[0] or 0
        except Exception as e:
            logger.error(f"Erro ao calcular valor pago por Diego-Ana: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular valor pago por Diego-Ana: {str(e)}")
    
    @cached(expiry=30, key_prefix="valor_pago_alex")
    def calcular_valor_pago_alex(self) -> float:
        """Calcular o valor total pago por Alex-Rute"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Usar SQL para calcular a soma diretamente
            cursor.execute("SELECT SUM(COALESCE(alex_rute, 0)) as total_alex FROM atividades")
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            # Retornar o valor total pago por Alex-Rute ou 0 se for NULL
            return result[0] or 0
        except Exception as e:
            logger.error(f"Erro ao calcular valor pago por Alex-Rute: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao calcular valor pago por Alex-Rute: {str(e)}")
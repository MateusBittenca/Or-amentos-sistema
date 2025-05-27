from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse , HTMLResponse
import os
from PIL import Image
import io
import json
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
import logging
from fastapi import status

# Importar de nossos módulos
from config import logger
from models import Activity, PendingActivity, PaidActivity, PaymentData, ExtractedData, User
from models import PasswordResetRequest, PasswordResetResponse, PasswordUpdateRequest, PasswordUpdateResponse
from database import get_db_connection, initialize_database
from utils.ocr import ComprovanteReader, processar_comprovante_ocr
from managers.comprovante import ComprovantesManager
from auth.auth_user import login_for_access_token, get_current_user, oauth2_scheme, require_auth
from auth.auth_user import generate_reset_token, reset_password
from utils.cache import clear_cache


# Inicializar app FastAPI
app = FastAPI(title="API de Gerenciamento de Despesas de Construção")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar o gerenciador
manager = ComprovantesManager()

# Inicializar o banco de dados na inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    """Inicializar recursos na inicialização da aplicação"""
    logger.info("Inicializando recursos da aplicação...")
    initialize_database()
    logger.info("Aplicação iniciada com sucesso")

@app.get("/")
def read_root():
    return {"message": "API de Gerenciamento de Despesas de Construção"}

@app.head("/")
def head_root():
    """Manipulador para requisições HEAD no caminho raiz"""
    return {"message": "API de Gerenciamento de Despesas de Construção"}

@app.get("/health")
def health_check():
    """Endpoint de verificação de saúde para monitoramento do serviço"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Verificação de saúde falhou: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.head("/health")
def head_health_check():
    """Manipulador HEAD para endpoint de verificação de saúde"""
    return {"status": "healthy"}

@app.get("/atividades", response_model=List[Activity])
def get_activities(_: bool = Depends(require_auth)):
    try:
        return manager.listar_atividades()
    except Exception as e:
        logger.error(f"Erro ao buscar atividades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades: {str(e)}")

@app.get("/atividades-pendentes", response_model=List[PendingActivity])
def get_pending_activities(_: bool = Depends(require_auth)):
    try:
        # Usar método otimizado do manager com cache
        return manager.listar_atividades_pendentes()
    except Exception as e:
        logger.error(f"Erro ao buscar atividades pendentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades pendentes: {str(e)}")

@app.get("/atividades-pagas", response_model=List[PaidActivity])
def get_paid_activities(_: bool = Depends(require_auth)):
    try:
        # Usar método otimizado do manager
        return manager.listar_atividades_pagas()
    except Exception as e:
        logger.error(f"Erro ao buscar atividades pagas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades pagas: {str(e)}")

@app.post("/update-status")
def update_status(_: bool = Depends(require_auth)):
    try:
        # Limpar cache após atualização
        clear_cache("activities")
        return manager.atualizar_status()
    except Exception as e:
        logger.error(f"Erro ao atualizar status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")

@app.post("/add-activity")
def add_activity(
    atividade: str = Form(...),
    valor: str = Form(...),
    setor: str = Form(...), 
    data: str = Form(...),
    _: bool = Depends(require_auth)
):
    logger.debug(f"Dados recebidos: atividade={atividade}, valor={valor}, setor={setor}, data={data}")
    
    try:
        # Converter valor de string para float, lidando com diferentes formatos de número
        try:
            valor_float = float(valor.replace(',', '.'))
        except ValueError:
            raise HTTPException(status_code=400, detail="O valor deve ser um número")
        
        result = manager.adicionar_atividade(data, valor_float, setor, atividade)
        # Limpar cache após adicionar atividade
        clear_cache("activities")
        logger.debug(f"Resultado da adição: {result}")
        return result
    except HTTPException as he:
        # Relançar exceções HTTP
        raise he
    except Exception as e:
        error_message = f"Erro no endpoint /add-activity: {str(e)}"
        logger.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)
    
@app.delete("/delete-activity/{id}")
def delete_activity(id: int, _: bool = Depends(require_auth)):
    """Excluir uma atividade pelo seu ID"""
    try:
        result = manager.excluir_atividade(id)
        # Limpar cache após exclusão
        clear_cache("activities")
        return result
    except HTTPException as he:
        # Relançar exceções HTTP
        raise he
    except Exception as e:
        logger.error(f"Erro ao excluir atividade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir atividade: {str(e)}")
    
@app.get("/valor-total")
def get_total_value(_: bool = Depends(require_auth)):
    """Calcular valor total da construção somando os valores das atividades"""
    try:
        total_value = manager.calcular_valor_total()
        return {"total": total_value}
    except Exception as e:
        logger.error(f"Erro ao calcular o valor total: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total: {str(e)}")

@app.get("/valor-total-pago")
def get_valor_pago(_: bool = Depends(require_auth)):
    """Calculate total amount paid by summing values in Alex-Rute and Diego-Ana columns"""
    try:
        total_pago = manager.calcular_valor_total_pago()
        return {"total_pago": total_pago}
    except Exception as e:
        logger.error(f"Erro ao calcular o valor total pago: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total pago: {str(e)}")

@app.get("/valor-pago-diego")
def get_valor_pago_diego(_: bool = Depends(require_auth)):
    try:
        total_pago_diego = manager.calcular_valor_pago_diego()
        return {"total_pago_diego": total_pago_diego}
    except Exception as e:
        logger.error(f"Erro ao calcular o total pago por diego-Ana : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o total pago por diego-Ana :  {str(e)}")

@app.get("/valor-pago-alex")
def get_valor_pago_alex(_: bool = Depends(require_auth)):
    try:
        total_pago_alex = manager.calcular_valor_pago_alex()
        return {"total_pago_alex": total_pago_alex}
    except Exception as e:
        logger.error(f"Erro ao calcular o total pago por Alex-Rute: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o total pago por Alex-Rute: {str(e)}")

@app.post("/process-receipt", response_model=ExtractedData)
async def process_receipt(file: UploadFile = File(...), _: bool = Depends(require_auth)):
    try:
        # Get file extension from filename
        extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
        
        # Read file contents
        contents = await file.read()
        
        # Process with OCR API
        texto_extraido = processar_comprovante_ocr(contents, filetype=extension)
        
        # Extract data from the text
        reader = ComprovanteReader()
        valor = reader.extrair_valor(texto_extraido)
        data = reader.extrair_data(texto_extraido)
        nome = reader.extrair_nome(texto_extraido)
        
        # Return extracted data
        return ExtractedData(
            value=valor,
            date=data,
            name=nome,
            full_text=texto_extraido
        )
    except Exception as e:
        logger.error(f"Erro ao processar o comprovante: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register-payment")
async def register_payment(payment: PaymentData, _: bool = Depends(require_auth)):
    try:
        # Validação básica dos dados
        if not payment.activity or not payment.payer or not payment.value:
            missing = []
            if not payment.activity: missing.append("atividade")
            if not payment.payer: missing.append("pagador")
            if not payment.value: missing.append("valor")
            raise HTTPException(status_code=400, detail=f"Campos obrigatórios faltando: {', '.join(missing)}")
            
        # Registrar pagamento
        result = manager.preencher_pagamento(
            payment.value,
            payment.activity,
            payment.payer,
            payment.sector,
            payment.date
        )
        
        # Limpar cache após pagamento
        clear_cache("activities")
        
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Erro ao registrar pagamento: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao registrar pagamento: {str(e)}")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint de autenticação para gerar token JWT"""
    return await login_for_access_token(form_data)

# Password reset endpoints
@app.post("/password/request-reset", response_model=PasswordResetResponse)
async def request_password_reset(request: PasswordResetRequest):
    """Solicitar redefinição de senha"""
    try:
        logger.info(f"Solicitação de redefinição de senha para usuário: {request.username}")
        response = generate_reset_token(request.username)
        return response
    except Exception as e:
        logger.error(f"Erro ao solicitar redefinição de senha: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar solicitação de redefinição de senha"
        )

@app.post("/password/reset", response_model=PasswordUpdateResponse)
async def confirm_password_reset(request: PasswordUpdateRequest):
    """Confirmar redefinição de senha com token"""
    try:
        logger.info(f"Confirmação de redefinição de senha para usuário: {request.username}")
        response = await reset_password(
            request.username,
            request.reset_token,
            request.new_password
        )
        return response
    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar redefinição de senha"
        )

# Run the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))  # Render define PORT dinamicamente
    uvicorn.run(app, host="0.0.0.0", port=port)
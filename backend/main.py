from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from PIL import Image
import io
import json
from typing import List
import logging

# Importar de nossos módulos
from config import logger
from models import Activity, PendingActivity, PaidActivity, PaymentData, ExtractedData
from database import get_db_connection, initialize_database
from utils.ocr import ComprovanteReader, processar_via_api_ocr
from managers.comprovante import ComprovantesManager

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

# Inicializar o banco de dados na inicialização
@app.on_event("startup")
async def startup_event():
    initialize_database()

# Inicializar o gerenciador
manager = ComprovantesManager()

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
def get_activities():
    try:
        return manager.listar_atividades()
    except Exception as e:
        logger.error(f"Erro ao buscar atividades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades: {str(e)}")

@app.get("/atividades-pendentes", response_model=List[PendingActivity])
def get_pending_activities():
    try:
        return manager.listar_atividades_pendentes()
    except Exception as e:
        logger.error(f"Erro ao buscar atividades pendentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades pendentes: {str(e)}")

@app.get("/atividades-pagas", response_model=List[PaidActivity])
def get_paid_activities():
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
        logger.error(f"Erro ao buscar atividades pagas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades pagas: {str(e)}")

@app.post("/update-status")
def update_status():
    try:
        return manager.atualizar_status()
    except Exception as e:
        logger.error(f"Erro ao atualizar status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")

@app.post("/add-activity")
def add_activity(
    atividade: str = Form(...),
    valor: str = Form(...),
    setor: str = Form(...), 
    data: str = Form(...)
):
    logger.debug(f"Dados recebidos: atividade={atividade}, valor={valor}, setor={setor}, data={data}")
    
    try:
        # Converter valor de string para float, lidando com diferentes formatos de número
        try:
            valor_float = float(valor.replace(',', '.'))
        except ValueError:
            raise HTTPException(status_code=400, detail="O valor deve ser um número")
        
        result = manager.adicionar_atividade(data, valor_float, setor, atividade)
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
def delete_activity(id: int):
    """Excluir uma atividade pelo seu ID"""
    try:
        result = manager.excluir_atividade(id)
        return result
    except HTTPException as he:
        # Relançar exceções HTTP
        raise he
    except Exception as e:
        logger.error(f"Erro ao excluir atividade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao excluir atividade: {str(e)}")
    
@app.get("/valor-total")
def get_total_value():
    """Calcular valor total da construção somando os valores das atividades"""
    try:
        total_value = manager.calcular_valor_total()
        return {"total": total_value}
    except Exception as e:
        logger.error(f"Erro ao calcular o valor total: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total: {str(e)}")

@app.get("/valor-total-pago")
def get_valor_pago():
    """Calculate total amount paid by summing values in Alex-Rute and Diego-Ana columns"""
    try:
        total_pago = manager.calcular_valor_total_pago()
        return {"total_pago": total_pago}
    except Exception as e:
        logger.error(f"Erro ao calcular o valor total pago: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total pago: {str(e)}")

@app.get("/valor-pago-diego")
def get_valor_pago_diego():
    try:
        total_pago_diego = manager.calcular_valor_pago_diego()
        return {"total_pago_diego": total_pago_diego}
    except Exception as e:
        logger.error(f"Erro ao calcular o total pago por diego-Ana : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o total pago por diego-Ana :  {str(e)}")

@app.get("/valor-pago-alex")
def get_valor_pago_alex():
    try:
        total_pago_alex = manager.calcular_valor_pago_alex()
        return {"total_pago_alex": total_pago_alex}
    except Exception as e:
        logger.error(f"Erro ao calcular o total pago por Alex-Rute: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o total pago por Alex-Rute: {str(e)}")

@app.post("/process-receipt", response_model=ExtractedData)
async def process_receipt(file: UploadFile = File(...)):
    try:
        # Get file extension from filename
        extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
        
        # Read file contents
        contents = await file.read()
        
        # Process with OCR API
        texto_extraido = processar_via_api_ocr(contents, filetype=extension)
        
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
def register_payment(payment: PaymentData):
    try:
        # Log details for diagnosis
        logger.debug(f"Received payment data: {payment.model_dump()}")
        
        # Validate received data
        if not payment.activity:
            raise HTTPException(status_code=400, detail="Activity name is required")
        if not payment.payer:
            raise HTTPException(status_code=400, detail="Payer is required")
        if not payment.value:
            raise HTTPException(status_code=400, detail="Payment value is required")
            
        # Log the value before conversion
        logger.debug(f"Payment value before processing: '{payment.value}'")
        
        # Register payment in JSON data (this might raise exceptions)
        try:
            result = manager.preencher_pagamento(
                payment.value,
                payment.activity,
                payment.payer,
                payment.sector,
                payment.date
            )
        except Exception as e:
            logger.error(f"Error in preencher_pagamento: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing payment: {str(e)}")
        
        # Update status after registering payment
        try:
            status_result = manager.atualizar_status()
            logger.debug(f"Status update result: {status_result}")
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}", exc_info=True)
            # Continue anyway since the payment was registered
        
        return {"message": "Payment registered successfully!", "result": result}
    except HTTPException as he:
        # Re-raise HTTP exceptions
        logger.error(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unhandled exception in register_payment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error registering payment: {str(e)}")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
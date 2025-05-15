from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from PIL import Image
import pytesseract
import re
import io
import json
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import logging
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "turntable.proxy.rlwy.net"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "SpDrzzWjYjYcvQDrlOldHkKLKMmmJRbt"),
    "database": os.getenv("DB_NAME", "railway"),
    "port": int(os.getenv("DB_PORT", "10713")),
}

# Pydantic models for request/response data
class Activity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    value: float
    date: Optional[str] = None
    diego_ana: Optional[float] = None
    alex_rute: Optional[float] = None
    
class PendingActivity(BaseModel):
    id: int  
    activity: str
    sector: Optional[str] = None
    total_value: float
    valor_restante: float
    date: Optional[str] = None
    diego_ana: float
    alex_rute: float

class PaidActivity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    total_value: float
    date: Optional[str] = None
    diego_ana: float
    alex_rute: float
    status: str
    
class PaymentData(BaseModel):
    activity: str
    sector: Optional[str] = None
    payer: str
    value: str
    date: Optional[str] = None

class ExtractedData(BaseModel):
    value: Optional[str] = None
    date: Optional[str] = None
    name: Optional[str] = None
    full_text: Optional[str] = None


class ComprovanteReader:
    """Class responsible for reading and extracting information from payment receipts"""
    
    @staticmethod
    def extrair_valor(texto: str) -> Optional[str]:
        """Extract monetary value from text"""
        match = re.search(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', texto)
        return match.group() if match else None

    @staticmethod
    def extrair_data(texto: str) -> Optional[str]:
        """Extract date in DD/MM/YYYY format from text"""
        match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
        return match.group() if match else None

    @staticmethod
    def extrair_nome(texto: str) -> Optional[str]:
        """Extract person name from text"""
        # Try to find name after keywords like "Titular", "Pagador", etc.
        match = re.search(r'(?:Titular|Pagador|Quem pagou|Nome do titular)\s*[:\-]?\s*([A-Za-z\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\bCPF\b.*', '', nome, flags=re.IGNORECASE).strip()
            return ' '.join([word.capitalize() for word in nome.split()])

        # Alternative pattern: look for name after "de"
        match = re.search(r'\bde\s([A-Za-z\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\bCPF\b.*', '', nome, flags=re.IGNORECASE).strip()
            return ' '.join([word.capitalize() for word in nome.split()])

        return None


def processar_via_api_ocr(contents, filetype="jpg"):
    """
    Process an image using the OCR.space API
    
    Args:
        contents: The binary contents of the image file
        filetype: The file type extension (jpg, png, pdf, etc.)
    """
    import requests
    import json
    
    api_key = "helloworld"  # Replace with your actual API key
    
    payload = {
        'apikey': api_key,
        'language': 'por',  # Assuming Portuguese language for OCR
        'isOverlayRequired': False,
        'filetype': filetype,  # Explicitly define the file type
    }
    
    files = {
        'file': contents  # Just send the binary contents
    }
    
    try:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files=files,
            data=payload
        )
        
        result = response.json()
        
        if result.get('OCRExitCode') == 1:  # Success
            extracted_text = result.get('ParsedResults')[0].get('ParsedText', '')
            return extracted_text
        else:
            raise Exception(f"OCR API error: {result.get('ErrorMessage', 'Unknown error')}")
    
    except Exception as e:
        raise Exception(f"Error processing OCR: {str(e)}")

# Database connection
def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Function to initialize the database tables
def initialize_database():
    """Initialize database tables if they don't exist"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create table for activities
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS atividades (
            idAtividades INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            setor VARCHAR(100),
            valor DECIMAL(10, 2) NOT NULL,
            data VARCHAR(20),
            alex_rute DECIMAL(10, 2) DEFAULT 0,
            diego_ana DECIMAL(10, 2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending'
        )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Database initialized successfully")
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(status_code=500, detail=f"Database initialization error: {str(e)}")

class ComprovantesManager:
    """Class to manage construction expenses in MySQL database"""
    
    def __init__(self):
        # This will be empty as we'll use DB connections as needed
        pass
    
    def _parse_value(self, value_str: str) -> float:
        """Convert string value to float, handling different formats"""
        try:
            # Log for diagnostic
            logger.debug(f"Parsing value: '{value_str}', type: {type(value_str)}")
            
            if isinstance(value_str, (int, float)):
                return float(value_str)
                    
            # Remove currency symbols and spaces
            clean_value = value_str.replace('R$', '').strip()
            logger.debug(f"Clean value after removing currency symbol: '{clean_value}'")
            
            # Replace separators - Brazilian format (1.234,56) to decimal point (1234.56)
            if ',' in clean_value:
                # If it has a comma, assume Brazilian format
                clean_value = clean_value.replace('.', '').replace(',', '.')
            
            logger.debug(f"Final clean value: '{clean_value}'")
            
            return float(clean_value)
        except ValueError as e:
            logger.error(f"Value parsing error for '{value_str}': {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid value format: {value_str}")
    
    def _format_date(self, date_str: str) -> str:
        """Format date to display format (DD/MM/YYYY)"""
        if not date_str:
            return None
            
        try:
            # Check if format is YYYY-MM-DD (from HTML type="date" input)
            if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                # Convert to DD/MM/YYYY for storing
                year, month, day = date_str.split('-')
                return f"{day}/{month}/{year}"
            elif re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                # Already in DD/MM/YYYY format
                return date_str
            else:
                logger.warning(f"Unknown date format: {date_str}")
                return date_str  # Return as is if format unknown
        except Exception as e:
            logger.error(f"Error formatting date {date_str}: {e}")
            return date_str  # Return as is if there's an error
    
    def preencher_pagamento(self, valor_str: str, atividade: str, pagador: str, 
                            setor: Optional[str] = None, data: Optional[str] = None) -> Dict[str, Any]:
        """Register a payment in the database"""
        # Convert value to float
        valor = self._parse_value(valor_str)
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Find matching activity
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
                raise HTTPException(status_code=404, detail=f"Activity '{atividade}' not found")
            
            # Determine which field to update based on payer
            field_to_update = ""
            if pagador.lower() in ['alex-rute', 'alex rute', 'alex', 'rute']:
                field_to_update = "alex_rute"
                new_value = (activity['alex_rute'] or 0) + valor
            elif pagador.lower() in ['diego-ana', 'diego ana', 'diego', 'ana']:
                field_to_update = "diego_ana"
                new_value = (activity['diego_ana'] or 0) + valor
            else:
                # Try to infer based on name extracted from receipt
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
                        detail=f"Payer '{pagador}' not recognized. Use 'Alex-Rute' or 'Diego-Ana'"
                    )
            
            # Update the field
            update_query = f"UPDATE atividades SET {field_to_update} = %s WHERE idAtividades = %s"
            cursor.execute(update_query, (new_value, activity['idAtividades']))
            
            # Update payment status
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
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error registering payment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error registering payment: {str(e)}")
            
    def atualizar_status(self) -> Dict[str, Any]:
        """Update payment status for all activities based on filled values"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Get all activities
            cursor.execute("SELECT * FROM atividades")
            activities = cursor.fetchall()
            
            updated_count = 0
            
            for activity in activities:
                value = activity['valor'] or 0
                alex_rute = activity['alex_rute'] or 0
                diego_ana = activity['diego_ana'] or 0
                
                # Calculate status
                status = "paid" if (alex_rute + diego_ana) >= value else "pending"
                
                # Update status
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
            logger.error(f"Error updating status: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")
    
    def listar_atividades_pendentes(self) -> List[PendingActivity]:
        """List all activities with pending payments"""
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
                
                # Calculate remaining amount to be paid
                valor_restante = valor_custo - (alex_rute + diego_ana)
                
                # Get date string directly from database
                date_str = activity['data']
                
                # Check if there's still a pending amount
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
            logger.error(f"Error listing pending activities: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing pending activities: {str(e)}")
    
    def listar_atividades(self) -> List[Activity]:
        """List all activities in the database"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM atividades")
            db_activities = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            activities_list = []
            
            for activity in db_activities:
                # Date is already stored as string
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
            logger.error(f"Error listing activities: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error listing activities: {str(e)}")
    
    def adicionar_atividade(self, data: str, valor: float, 
                           setor: str, atividade: str) -> Dict[str, Any]:
        """Add a new activity to the database"""
        try:
            logger.debug(f"Adicionando atividade: data={data}, valor={valor}, setor={setor}, atividade={atividade}")
            
            # Format date string for storage
            date_str = self._format_date(data) if data else None
            
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Insert new activity
            query = """
            INSERT INTO atividades (nome, setor, valor, data, alex_rute, diego_ana, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (atividade, setor, float(valor), date_str, 0, 0, "pending"))
            
            # Get the ID of the inserted row
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
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Erro inesperado ao adicionar a atividade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao adcionar a atividade: {str(e)}")
        
    def excluir_atividade(self, id: int) -> Dict[str, Any]:
        """Delete an activity by its ID"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Check if activity exists
            cursor.execute("SELECT nome FROM atividades WHERE idAtividades = %s", (id,))
            activity = cursor.fetchone()
            
            if not activity:
                cursor.close()
                connection.close()
                raise HTTPException(status_code=404, detail="Activity not found")
            
            # Delete activity
            cursor.execute("DELETE FROM atividades WHERE idAtividades = %s", (id,))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "message": f"Atividade: '{activity['nome']}' removida com sucesso!"
            }
        except HTTPException as he:
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error deleting activity: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error deleting activity: {str(e)}")
            
    def calcular_valor_total(self) -> float:
        """Calculate total value of construction by summing activity values"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(valor) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Error calculating total value: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error calculating total value: {str(e)}")
    
    def calcular_valor_total_pago(self) -> float:
        """Calculate total amount paid by summing values in Alex-Rute and Diego-Ana columns"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(alex_rute) + SUM(diego_ana) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Error calculating total paid: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error calculating total paid: {str(e)}")
    
    def calcular_valor_pago_diego(self) -> float:
        """Calculate total amount paid by Diego-Ana"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(diego_ana) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Error calculating total paid by Diego-Ana: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error calculating total paid by Diego-Ana: {str(e)}")

    def calcular_valor_pago_alex(self) -> float:
        """Calculate total amount paid by Alex-Rute"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT SUM(alex_rute) FROM atividades")
            total = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return float(total) if total else 0
        except Exception as e:
            logger.error(f"Error calculating total paid by Alex-Rute: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error calculating total paid by Alex-Rute: {str(e)}")


# Initialize FastAPI app
app = FastAPI(title="Construction Expense Manager API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database on startup
@app.on_event("startup")
async def startup_event():
    initialize_database()

# Initialize the manager
manager = ComprovantesManager()

@app.get("/")
def read_root():
    return {"message": "Construction Expense Manager API"}

@app.head("/")
def head_root():
    """Handler for HEAD requests to the root path"""
    return {"message": "Construction Expense Manager API"}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.head("/health")
def head_health_check():
    """HEAD handler for health check endpoint"""
    return {"status": "healthy"}

@app.get("/atividades", response_model=List[Activity])
def get_activities():
    try:
        return manager.listar_atividades()
    except Exception as e:
        logger.error(f"Error fetching activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")

@app.get("/atividades-pendentes", response_model=List[PendingActivity])
def get_pending_activities():
    try:
        return manager.listar_atividades_pendentes()
    except Exception as e:
        logger.error(f"Error fetching pending activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching pending activities: {str(e)}")

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
            # Date is already stored as string
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
        logger.error(f"Error fetching paid activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching paid activities: {str(e)}")


@app.post("/update-status")
def update_status():
    try:
        return manager.atualizar_status()
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

@app.post("/add-activity")
def add_activity(
    atividade: str = Form(...),
    valor: str = Form(...),
    setor: str = Form(...), 
    data: str = Form(...)
):
    logger.debug(f"Received data: activity={atividade}, value={valor}, sector={setor}, date={data}")
    
    try:
        # Convert string value to float, handling different number formats
        try:
            valor_float = float(valor.replace(',', '.'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Value must be a number")
        
        result = manager.adicionar_atividade(data, valor_float, setor, atividade)
        logger.debug(f"Resultado da adição: {result}")
        return result
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        error_message = f"Erro no endpoint /add-activity: {str(e)}"
        logger.error(error_message, exc_info=True)
        raise HTTPException(status_code=500, detail=error_message)
    
@app.delete("/delete-activity/{id}")
def delete_activity(id: int):
    """Delete an activity by its ID"""
    try:
        result = manager.excluir_atividade(id)
        return result
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Error deleting activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting activity: {str(e)}")

@app.get("/valor-total")
def get_total_value():
    """Calculate total construction value by summing activity values"""
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
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
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

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
UPLOAD_FOLDER = "uploads"
JSON_PATH = "./json/atividades.json"

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    @classmethod
    def ler_comprovante(cls, imagem_bytes: bytes) -> Dict[str, Any]:
        """Read a receipt from image bytes and extract relevant information"""
        try:
            with Image.open(io.BytesIO(imagem_bytes)) as imagem:
                texto = pytesseract.image_to_string(imagem, lang='eng')
                
                return {
                    'texto_completo': texto,
                    'valor': cls.extrair_valor(texto),
                    'data': cls.extrair_data(texto),
                    'nome': cls.extrair_nome(texto)
                }
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


class ComprovantesManager:
    """Class to manage construction expenses in a JSON file"""
    
    def __init__(self, json_path: str):
        self.json_path = json_path
        
        # Initialize data structure
        self.data = {
            "activities": []
        }
        
        # Ensure the file exists
        if not os.path.exists(json_path):
            self._create_json_template()
        else:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading JSON file: {e}", exc_info=True)
                # Create a new file if there's an error
                self._create_json_template()
    
    def _create_json_template(self) -> None:
        """Create a new JSON file with the expected structure"""
        self.data = {
            "activities": []
        }
        self._save_data()
    
    def _find_activity_index(self, activity: str, sector: Optional[str] = None) -> Optional[int]:
        """Find the index of an activity in the data list"""
        for idx, item in enumerate(self.data["activities"]):
            if item["activity"].strip().lower() == activity.strip().lower():
                if sector is None or (item.get("sector", "").strip().lower() == sector.strip().lower()):
                    return idx
        return None
    
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
    
    def _save_data(self) -> None:
        """Save data to JSON file with error handling"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except PermissionError:
            logger.error(f"Permission error while saving JSON file: {self.json_path}")
            raise HTTPException(
                status_code=500, 
                detail="Could not save JSON file. It may be open in another program."
            )
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error saving JSON file: {str(e)}")
    
    def preencher_pagamento(self, valor_str: str, atividade: str, pagador: str, 
                            setor: Optional[str] = None, data: Optional[str] = None) -> Dict[str, Any]:
        """Register a payment in the JSON data"""
        # Convert value to float
        valor = self._parse_value(valor_str)
        
        # Find matching activity
        idx = self._find_activity_index(atividade, setor)
        
        if idx is None:
            raise HTTPException(status_code=404, detail=f"Activity '{atividade}' not found")
        
        # Determine which field to update based on payer
        if pagador.lower() in ['alex-rute', 'alex rute', 'alex', 'rute']:
            self.data["activities"][idx]["alex_rute"] = (self.data["activities"][idx].get("alex_rute", 0) or 0) + valor
        elif pagador.lower() in ['diego-ana', 'diego ana', 'diego', 'ana']:
            self.data["activities"][idx]["diego_ana"] = (self.data["activities"][idx].get("diego_ana", 0) or 0) + valor
        else:
            # Try to infer based on name extracted from receipt
            if 'alex' in pagador.lower() or 'rute' in pagador.lower():
                self.data["activities"][idx]["alex_rute"] = (self.data["activities"][idx].get("alex_rute", 0) or 0) + valor
            elif 'diego' in pagador.lower() or 'ana' in pagador.lower():
                self.data["activities"][idx]["diego_ana"] = (self.data["activities"][idx].get("diego_ana", 0) or 0) + valor
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Payer '{pagador}' not recognized. Use 'Alex-Rute' or 'Diego-Ana'"
                )
        
        # Update payment status
        self.data["activities"][idx]["status"] = self._calculate_status(idx)
        
        # Save changes
        self._save_data()
        
        return {
            "sucesso": True,
            "mensagem": f"Pagamento no valor de R$ {valor:.2f} Registrado na atividade : '{atividade}' por {pagador}",
            "data": data
        }
    
    def _calculate_status(self, idx: int) -> str:
        """Calculate if an activity is fully paid or not"""
        activity = self.data["activities"][idx]
        value = activity.get("value", 0)
        alex_rute = activity.get("alex_rute", 0) or 0
        diego_ana = activity.get("diego_ana", 0) or 0
        
        return "paid" if (alex_rute + diego_ana) >= value else "pending"
        
    def atualizar_status(self) -> Dict[str, Any]:
        """Update payment status for all activities based on filled values"""
        updated_count = 0
        
        for idx, activity in enumerate(self.data["activities"]):
            value = activity.get("value", 0)
            alex_rute = activity.get("alex_rute", 0) or 0
            diego_ana = activity.get("diego_ana", 0) or 0
            
            # Calculate status
            status = "paid" if (alex_rute + diego_ana) >= value else "pending"
            
            # Update status
            self.data["activities"][idx]["status"] = status
            updated_count += 1
        
        # Save changes
        self._save_data()
        
        return {
            "success": True,
            "message": "Payment status updated successfully",
            "updated_rows": updated_count
        }
    
    def listar_atividades_pendentes(self) -> List[PendingActivity]:
        """List all activities with pending payments"""
        atividades_pendentes = []

        for idx, activity in enumerate(self.data["activities"]):
            valor_custo = activity.get("value", 0)
            alex_rute = activity.get("alex_rute", 0) or 0
            diego_ana = activity.get("diego_ana", 0) or 0

            # Calculate remaining amount to be paid
            valor_restante = valor_custo - (alex_rute + diego_ana)

            # Check if there's still a pending amount
            if valor_restante > 0:
                atividades_pendentes.append(PendingActivity(
                    id=idx,
                    activity=activity.get("activity", ""),
                    sector=activity.get("sector", ""),
                    total_value=valor_custo,
                    valor_restante=valor_restante,
                    date=activity.get("date", None),
                    alex_rute=alex_rute,
                    diego_ana=diego_ana
                ))

        return atividades_pendentes
    
    def listar_atividades(self) -> List[Activity]:
        """List all activities in the data"""
        activities_list = []
        
        for idx, activity in enumerate(self.data["activities"]):
            activities_list.append(Activity(
                id=idx,
                activity=activity.get("activity", ""),
                sector=activity.get("sector", ""),
                value=activity.get("value", 0),
                date=activity.get("date", None),
                diego_ana=activity.get("diego_ana", 0) or 0,
                alex_rute=activity.get("alex_rute", 0) or 0
            ))
        
        return activities_list
    
    def adicionar_atividade(self, data: Union[str, datetime], valor: float, 
                           setor: str, atividade: str) -> Dict[str, Any]:
        """Add a new activity to the data"""
        try:
            logger.debug(f"Adicionando atividade: data={data}, valor={valor}, setor={setor}, atividade={atividade}")
            
            # Format date if it's a string
            date_str = None
            if isinstance(data, str):
                # Check if format is YYYY-MM-DD (from HTML type="date" input)
                if re.match(r'\d{4}-\d{2}-\d{2}', data):
                    date_obj = datetime.strptime(data, "%Y-%m-%d")
                    date_str = date_obj.strftime("%d/%m/%Y")
                else:
                    # Assume it's already in DD/MM/YYYY format
                    date_str = data
            elif isinstance(data, datetime):
                date_str = data.strftime("%d/%m/%Y")
            
            # Create new activity object
            new_activity = {
                "activity": atividade,
                "sector": setor,
                "value": float(valor),
                "date": date_str,
                "alex_rute": 0,
                "diego_ana": 0,
                "status": "pending"
            }
            
            # Add to list
            self.data["activities"].append(new_activity)
            
            # Save changes
            self._save_data()
            
            return {
                "success": True,
                "mensagem": f"Atividade: '{atividade}' adicionada com sucesso",
                "id": len(self.data["activities"]) - 1,
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
            if id < 0 or id >= len(self.data["activities"]):
                raise HTTPException(status_code=404, detail="Activity not found")
            
            # Remove activity
            removed_activity = self.data["activities"].pop(id)
            
            # Save changes
            self._save_data()
            
            return {
                "success": True,
                "message": f"Atividade: '{removed_activity['activity']}' removida com sucesso!"
            }
        except HTTPException as he:
            # Re-raise HTTP exceptions
            raise he
        except Exception as e:
            logger.error(f"Error deleting activity: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error deleting activity: {str(e)}")

            
    def calcular_valor_total(self) -> float:
        """Calculate total value of construction by summing activity values"""
        return sum(activity.get("value", 0) or 0 for activity in self.data["activities"])
    
    def calcular_valor_total_pago(self) -> float:
        """Calculate total amount paid by summing values in Alex-Rute and Diego-Ana columns"""
        total = 0
        for activity in self.data["activities"]:
            total += (activity.get("alex_rute", 0) or 0) + (activity.get("diego_ana", 0) or 0)
        return total
    
    def calcular_valor_pago_diego(self) -> float:
        """Calculate total amount paid by Diego-Ana"""
        return sum(activity.get("diego_ana", 0) or 0 for activity in self.data["activities"])

    def calcular_valor_pago_alex(self) -> float:
        """Calculate total amount paid by Alex-Rute"""
        return sum(activity.get("alex_rute", 0) or 0 for activity in self.data["activities"])


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

# Initialize the manager
manager = ComprovantesManager(JSON_PATH)

@app.get("/")
def read_root():
    return {"message": "Construction Expense Manager API"}

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
        logger.debug(f"Arquivo recebido: {file.filename}, tipo: {file.content_type}")
        # Read uploaded file
        contents = await file.read()
        # Process receipt image
        result = ComprovanteReader.ler_comprovante(contents)
        # Return extracted data
        return ExtractedData(
            value=result['valor'],
            date=result['data'],
            name=result['nome'],
            full_text=result['texto_completo']
        )
    except Exception as e:
        logger.error(f"Erro ao processar o comprovante {e}", exc_info=True)
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
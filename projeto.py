# app.py - FastAPI Backend for Construction Expense Manager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill
import os
from PIL import Image
import pytesseract
import re
import io
import tempfile
import shutil
import uuid
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Construction Expense Manager API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers

)

# Configuration
UPLOAD_FOLDER = "uploads"
EXCEL_PATH = "Fluxo Caixa Construção Guaratinguetá.xlsx"

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Pydantic models for request/response data
class Activity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    value: float
    
class PendingActivity(BaseModel):
    id: int  
    activity: str
    sector: Optional[str] = None
    total_value: float


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
    @staticmethod
    def extrair_valor(texto):
        match = re.search(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', texto)
        if match:
            return match.group()
        return None

    @staticmethod
    def extrair_data(texto):
        match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
        if match:
            return match.group()
        return None

    @staticmethod
    def extrair_nome(texto):
        match = re.search(r'(?:Titular|Pagador|Quem pagou|Nome do titular)\s*[:\-]?\s*([A-Za-z\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\bCPF\b.*', '', nome, flags=re.IGNORECASE).strip()
            return ' '.join([word.capitalize() for word in nome.split()])

        match = re.search(r'\bde\s([A-Za-z\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\bCPF\b.*', '', nome, flags=re.IGNORECASE).strip()
            return ' '.join([word.capitalize() for word in nome.split()])

        return None

    @classmethod
    def ler_comprovante(cls, imagem_bytes):
        """Lê um comprovante a partir de bytes de imagem e extrai as informações relevantes"""
        try:
            with Image.open(io.BytesIO(imagem_bytes)) as imagem:
                texto = pytesseract.image_to_string(imagem, lang='eng')
                
                valor = cls.extrair_valor(texto)
                data = cls.extrair_data(texto)
                nome = cls.extrair_nome(texto)
                
                return {
                    'texto_completo': texto,
                    'valor': valor,
                    'data': data,
                    'nome': nome
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


class ComprovantesManager:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        # Ensure the file exists
        if not os.path.exists(excel_path):
            # Create new Excel file with basic structure if it doesn't exist
            self._create_excel_template()
            
        # Load the Excel file, maintaining existing formatting
        self.workbook = openpyxl.load_workbook(excel_path)
        self.sheet = self.workbook.active
        
        # Define colors for formatting
        self.verde = PatternFill(start_color="92D050", end_color="92D050", fill_type="solid")
        self.vermelho = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        
        # Load data to pandas for easier manipulation
        self.df = pd.read_excel(excel_path)
    
    def _create_excel_template(self):
        """Create a new Excel file with the expected structure"""
        wb = openpyxl.Workbook()
        ws = wb.active
        
        # Set headers
        headers = ["Referência", "Valor", "Setor", "Atividade", "Alex-Rute", "Diego-Ana", "Data"]
        for col_num, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_num).value = header
        
        # Save the file
        wb.save(self.excel_path)
        
    def preencher_pagamento(self, valor_str, atividade, pagador, setor=None, data=None):
        """
        Preenche a tabela com os dados do comprovante
        
        Args:
            valor_str (str): Valor do pagamento extraído do comprovante (formato: R$ X.XXX,XX)
            atividade (str): Descrição da atividade
            pagador (str): Quem pagou (Alex-Rute ou Diego-Ana)
            setor (str, optional): Setor relacionado ao pagamento
            data (str, optional): Data do pagamento no formato DD/MM/AAAA
        """
        # Converter o valor de string para float
        valor_str = valor_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        try:
            valor = float(valor_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Error converting value: {valor_str}")
        
        # Procurar linha com a atividade especificada na coluna D
        linhas_encontradas = []
        for i in range(2, self.sheet.max_row + 1):
            atividade_celula = self.sheet[f'D{i}'].value
            if atividade_celula and atividade_celula.strip().lower() == atividade.strip().lower():
                linhas_encontradas.append(i)
        
        # Se setor for especificado, filtrar também pelo setor
        if setor and len(linhas_encontradas) > 1:
            linhas_com_setor = []
            for linha in linhas_encontradas:
                setor_celula = self.sheet[f'C{linha}'].value
                if setor_celula and setor_celula.strip().lower() == setor.strip().lower():
                    linhas_com_setor.append(linha)
            if linhas_com_setor:
                linhas_encontradas = linhas_com_setor
        
        if not linhas_encontradas:
            raise HTTPException(status_code=404, detail=f"Activity '{atividade}' not found in the table")
        
        # Para simplificar, vamos usar a primeira linha encontrada
        linha_excel = linhas_encontradas[0]
        
        # Determinar a coluna para preenchimento
        coluna = None
        if pagador.lower() in ['alex-rute', 'alex rute', 'alex', 'rute']:
            coluna = 'E'  # Coluna Alex-Rute
        elif pagador.lower() in ['diego-ana', 'diego ana', 'diego', 'ana']:
            coluna = 'F'  # Coluna Diego-Ana
        else:
            # Tentar inferir com base no nome extraído do comprovante
            if 'alex' in pagador.lower() or 'rute' in pagador.lower():
                coluna = 'E'
            elif 'diego' in pagador.lower() or 'ana' in pagador.lower():
                coluna = 'F'
            else:
                raise HTTPException(status_code=400, detail=f"Payer '{pagador}' not recognized. Use 'Alex-Rute' or 'Diego-Ana'")
        
        # Preencher o valor na célula apropriada
        self.sheet[f'{coluna}{linha_excel}'] = valor
        
        # Se a data foi fornecida, preencha em uma coluna específica
        if data:
            self.sheet[f'G{linha_excel}'] = data
        
        # Aplicar formatação verde (pago) à linha
        for col in range(1, 7):  # Colunas A a F
            coluna_letra = openpyxl.utils.get_column_letter(col)
            self.sheet[f'{coluna_letra}{linha_excel}'].fill = self.verde
        
        # Salvar as alterações
        self.workbook.save(self.excel_path)
        
        return {
            "success": True,
            "message": f"Payment of R$ {valor:.2f} registered for '{atividade}' by {pagador}",
            "date": data
        }
    
    def atualizar_status(self):
        """Atualiza o status de pagamento de todas as linhas com base nos valores preenchidos"""
        # Para cada linha na tabela (exceto cabeçalho)
        updated_rows = 0
        
        for i in range(2, self.sheet.max_row + 1):
            valor_custo = self.sheet[f'B{i}'].value
            if valor_custo is None or not isinstance(valor_custo, (int, float)):
                continue
                
            alex_rute = self.sheet[f'E{i}'].value or 0
            diego_ana = self.sheet[f'F{i}'].value or 0
            
            # Verificar se o valor total foi pago
            valor_pago = 0
            if isinstance(alex_rute, (int, float)):
                valor_pago += alex_rute
            if isinstance(diego_ana, (int, float)):
                valor_pago += diego_ana
            
            # Definir cor com base no status de pagamento
            cor = self.verde if valor_pago >= valor_custo else self.vermelho
            
            # Aplicar cor à linha inteira
            for col in range(1, 7):  # Colunas A a F
                coluna_letra = openpyxl.utils.get_column_letter(col)
                self.sheet[f'{coluna_letra}{i}'].fill = cor
            
            updated_rows += 1
        
        # Salvar as alterações
        self.workbook.save(self.excel_path)
        
        return {
            "success": True,
            "message": "Payment status updated successfully",
            "updated_rows": updated_rows
        }
    
    def listar_atividades_pendentes(self):
        """Lista todas as atividades que ainda estão pendentes de pagamento."""
        atividades_pendentes = []

        for i in range(2, self.sheet.max_row + 1):
            valor_custo = self.sheet[f'B{i}'].value
            if valor_custo is None or not isinstance(valor_custo, (int, float)):
                continue

            alex_rute = self.sheet[f'E{i}'].value or 0
            diego_ana = self.sheet[f'F{i}'].value or 0

            # Verificar se a soma de Alex-Rute e Diego-Ana é igual ao custo
            if alex_rute + diego_ana < valor_custo:
                atividade = self.sheet[f'D{i}'].value
                setor = self.sheet[f'C{i}'].value
                data = self.sheet[f'A{i}'].value

                atividades_pendentes.append(PendingActivity(
                    id=i - 1,  # Use o índice da linha como ID
                    activity=atividade,
                    sector=setor,
                    total_value=valor_custo
                ))

        return atividades_pendentes
    
    def listar_atividades(self):
        """Lista todas as atividades disponíveis na tabela"""
        atividades = []
        
        # Para cada linha na tabela (exceto cabeçalho)
        for i in range(2, self.sheet.max_row + 1):
            atividade = self.sheet[f'D{i}'].value
            setor = self.sheet[f'C{i}'].value
            valor_custo = self.sheet[f'B{i}'].value
            data = self.sheet[f'A{i}'].value
            
            if atividade and valor_custo:
                # Garantir que o valor seja um número
                if isinstance(valor_custo, str):
                    try:
                        valor_custo = float(valor_custo.replace('R$', '').replace('.', '').replace(',', '.').strip())
                    except ValueError:
                        # Se não conseguir converter, pular esta linha
                        continue
                
                atividades.append(Activity(
                    id=i-1,
                    activity=atividade,
                    sector=setor,
                    value=valor_custo          
                ))
        
        return atividades
    
    def adicionar_atividade(self, referencia, valor, setor, atividade):
        """Adiciona uma nova atividade à tabela"""
        # Find the next available row
        next_row = self.sheet.max_row + 1
        
        # Add the new activity
        self.sheet[f'A{next_row}'] = referencia
        self.sheet[f'B{next_row}'] = valor
        self.sheet[f'C{next_row}'] = setor
        self.sheet[f'D{next_row}'] = atividade
        
        # Apply red formatting (unpaid)
        for col in range(1, 7):  # Columns A to F
            column_letter = openpyxl.utils.get_column_letter(col)
            self.sheet[f'{column_letter}{next_row}'].fill = self.vermelho
        
        # Save changes
        self.workbook.save(self.excel_path)
        
        return {
            "success": True,
            "message": f"Atividade '{atividade}' Adicionada com sucesso!",
            "id": next_row - 1
        }


# Initialize the manager
manager = ComprovantesManager(EXCEL_PATH)

@app.get("/")
def read_root():
    return {"message": "Construction Expense Manager API"}

@app.get("/atividades", response_model=List[Activity])
def get_activities():
    return manager.listar_atividades()

@app.get("/atividades-pendentes", response_model=List[PendingActivity])
def get_pending_activities():
    return manager.listar_atividades_pendentes()

@app.post("/update-status")
def update_status():
    return manager.atualizar_status()

@app.post("/add-activity")
def add_activity(referencia: str = Form(...), 
                valor: float = Form(...), 
                setor: str = Form(...), 
                atividade: str = Form(...)):
    return manager.adicionar_atividade(referencia, valor, setor, atividade)

@app.get("/valor-total")
def get_total_value():
    """Calcula o valor total da obra somando os valores das atividades"""
    try:
        total_value = 0
        for i in range(2, manager.sheet.max_row + 1):  # Ignorar cabeçalho
            valor_custo = manager.sheet[f'B{i}'].value
            if isinstance(valor_custo, (int, float)):
                total_value += valor_custo

        return {"total": total_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total: {str(e)}")

@app.post("/process-receipt", response_model=ExtractedData)
async def process_receipt(file: UploadFile = File(...)):
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Process the receipt image
        result = ComprovanteReader.ler_comprovante(contents)
        
        # Return extracted data
        return ExtractedData(
            value=result['valor'],
            date=result['data'],
            name=result['nome'],
            full_text=result['texto_completo']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register-payment")
def register_payment(payment: PaymentData):
    result = manager.preencher_pagamento(
        payment.value,
        payment.activity,
        payment.payer,
        payment.sector,
        payment.date
    )
    
    # Update status after registering payment
    manager.atualizar_status()
    
    return result

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
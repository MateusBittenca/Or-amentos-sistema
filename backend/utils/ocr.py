import re
import requests
import base64
import json
from fastapi import HTTPException
from config import logger
import io

class ComprovanteReader:
    """Classe responsável por ler e extrair informações de comprovantes de pagamento"""

    @staticmethod
    def extrair_valor(texto: str):
        match = re.search(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', texto)
        return match.group() if match else None

    @staticmethod
    def extrair_data(texto: str):
        match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
        return match.group() if match else None

    @staticmethod
    def extrair_nome(texto: str):
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

def processar_comprovante_ocr(contents, filetype="jpg"):
    """
    Processa uma imagem com API OCR
    Args:
        contents: conteúdo binário da imagem (ex: file.read())
        filetype: tipo do arquivo (jpg, png, pdf, etc)
    Returns:
        Texto extraído da imagem
    """
    try:
        # Configurações da API OCR
        API_KEY = "helloworld"  # Substitua pela sua chave de API
        API_URL = "https://api.ocr.space/parse/image"
        
        # Codifica a imagem em base64
        encoded_image = base64.b64encode(contents).decode('utf-8')
        
        # Prepara os dados para envio
        payload = {
            'apikey': API_KEY,
            'base64Image': f"data:image/{filetype};base64,{encoded_image}",
            'language': 'por',  # Português, use 'eng' para inglês
            'isOverlayRequired': False,
            'filetype': filetype,
            'detectOrientation': True,
            'scale': True,
        }
        
        # Faz a requisição para a API
        headers = {'Content-Type': 'application/json'}
        response = requests.post(API_URL, json=payload, headers=headers)
        
        # Verifica o status da resposta
        if response.status_code != 200:
            logger.error(f"Erro na API OCR: Status {response.status_code}")
            raise HTTPException(status_code=500, detail="Erro ao processar imagem com API OCR")
        
        # Extrai o texto da resposta JSON
        result = response.json()
        
        if result.get("IsErroredOnProcessing", False):
            error_message = result.get("ErrorMessage", "Erro desconhecido na API OCR")
            logger.error(f"Erro no processamento OCR: {error_message}")
            raise HTTPException(status_code=500, detail=error_message)
        
        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return ""
        
        extracted_text = parsed_results[0].get("ParsedText", "")
        return extracted_text
    
    except Exception as e:
        logger.error(f"Erro ao processar OCR com API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar OCR: {str(e)}")
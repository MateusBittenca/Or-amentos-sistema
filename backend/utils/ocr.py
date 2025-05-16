import re
from fastapi import HTTPException
from config import logger

class ComprovanteReader:
    """Classe responsável por ler e extrair informações de comprovantes de pagamento"""
    
    @staticmethod
    def extrair_valor(texto: str):
        """Extrair valor monetário do texto"""
        match = re.search(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', texto)
        return match.group() if match else None

    @staticmethod
    def extrair_data(texto: str):
        """Extrair data no formato DD/MM/AAAA do texto"""
        match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
        return match.group() if match else None

    @staticmethod
    def extrair_nome(texto: str):
        """Extrair nome da pessoa do texto"""
        # Tentar encontrar nome após palavras-chave como "Titular", "Pagador", etc.
        match = re.search(r'(?:Titular|Pagador|Quem pagou|Nome do titular)\s*[:\-]?\s*([A-Za-z\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\bCPF\b.*', '', nome, flags=re.IGNORECASE).strip()
            return ' '.join([word.capitalize() for word in nome.split()])

        # Padrão alternativo: procurar nome após "de"
        match = re.search(r'\bde\s([A-Za-z\s]+)', texto, re.IGNORECASE)
        if match:
            nome = match.group(1).strip()
            nome = re.sub(r'\bCPF\b.*', '', nome, flags=re.IGNORECASE).strip()
            return ' '.join([word.capitalize() for word in nome.split()])

        return None

def processar_via_api_ocr(contents, filetype="jpg"):
    """
    Processar uma imagem usando a API OCR.space
    
    Args:
        contents: O conteúdo binário do arquivo de imagem
        filetype: A extensão do tipo de arquivo (jpg, png, pdf, etc.)
    """
    import requests
    import json
    
    api_key = "helloworld"  # Substitua pela sua chave de API real
    
    payload = {
        'apikey': api_key,
        'language': 'por',  # Assumindo linguagem portuguesa para OCR
        'isOverlayRequired': False,
        'filetype': filetype,  # Definir explicitamente o tipo de arquivo
    }
    
    files = {
        'file': contents  # Apenas enviar o conteúdo binário
    }
    
    try:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files=files,
            data=payload
        )
        
        result = response.json()
        
        if result.get('OCRExitCode') == 1:  # Sucesso
            extracted_text = result.get('ParsedResults')[0].get('ParsedText', '')
            return extracted_text
        else:
            raise Exception(f"Erro da API OCR: {result.get('ErrorMessage', 'Erro desconhecido')}")
    
    except Exception as e:
        raise Exception(f"Erro ao processar OCR: {str(e)}")
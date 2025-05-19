import re
from fastapi import HTTPException
from config import logger
from PIL import Image
import pytesseract
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
    Processa uma imagem com Tesseract OCR local
    Args:
        contents: conteúdo binário da imagem (ex: file.read())
        filetype: tipo do arquivo, ignorado neste caso
    Returns:
        Texto extraído da imagem
    """
    try:
        image = Image.open(io.BytesIO(contents))
        texto = pytesseract.image_to_string(image, lang='por')
        return texto
    except Exception as e:
        raise Exception(f"Erro ao processar OCR com Tesseract: {str(e)}")

from PIL import Image
import pytesseract
import re

imagem = Image.open("./img/comprovante2.jpg")

texto = pytesseract.image_to_string(imagem, lang='eng')

def extrair_valor(valor):
    match = re.search(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', valor)
    if match:
        return match.group()
    return "Valor não encontrado"

def extrair_data(data):
    match = re.search(r'\d{2}/\d{2}/\d{4}', data)
    if match:
        return match.group()
    return "Data não encontrada"

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

    return "Nome do titular não encontrado"

print("\nValor identificado:")
print(extrair_valor(texto))
print("\nData identificada:")
print(extrair_data(texto))
print("\nNome identificado:")
print(extrair_nome(texto))
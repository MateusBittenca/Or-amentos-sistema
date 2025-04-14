from PIL import Image
import pytesseract
import re

imagem = Image.open("./img/comprovante.jpg")


texto = pytesseract.image_to_string(imagem, lang='eng')

def extrair_valor(texto):
    match = re.search(r'R?\$?\s?\d{1,3}(?:\.\d{3})*,\d{2}', texto)
    if match:
        return match.group()
    return "Valor não encontrado"


print("Texto extraído:")
print(texto)
print("\nValor identificado:")
print(extrair_valor(texto))


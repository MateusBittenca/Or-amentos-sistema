FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# Instalar Tesseract e dependências
RUN apt-get update -y && \
    apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-por \
    tesseract-ocr-eng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar tudo para dentro da imagem
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta (ajustada para o padrão Render)
EXPOSE 10000

# Comando para rodar o servidor web (ajuste se necessário)
CMD ["python", "backend/main.py"]

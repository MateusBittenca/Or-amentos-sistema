#!/usr/bin/env bash
# Exit on error
set -o errexit

# Instalar Tesseract OCR e suas dependências
apt-get update -y
apt-get install -y tesseract-ocr
apt-get install -y libtesseract-dev 
apt-get install -y tesseract-ocr-por  # Para suporte em português
apt-get install -y tesseract-ocr-eng  # Suporte em inglês

# Instalar pacotes Python do requirements.txt
pip install -r requirements.txt

# Verificar instalação do Tesseract
tesseract --version
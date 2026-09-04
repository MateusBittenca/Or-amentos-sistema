FROM node:20-alpine AS frontend
WORKDIR /web
COPY frontend-app/package.json frontend-app/package-lock.json ./
RUN npm ci
COPY frontend-app/ ./
RUN npm run build

FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-por \
    tesseract-ocr-eng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
COPY --from=frontend /web/dist /app/frontend-app/dist

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "backend/main.py"]

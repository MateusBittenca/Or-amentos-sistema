# Sistema de Gestão de Gastos de Obra

Sistema para famílias e sócios acompanharem o orçamento de uma construção: atividades (despesas previstas), pagamentos com comprovante, papéis por obra e relatórios.

## Stack

- **Backend:** Python 3.10+, FastAPI, MySQL 8, JWT, bcrypt, Tesseract OCR
- **Frontend:** React 19, Vite, React Router, Tailwind CSS, Chart.js
- **Infra:** Docker Compose (app + MySQL)

## Como rodar

### Desenvolvimento local

1. Suba o MySQL (`docker compose up db` ou o compose completo).
2. Copie [`.env.example`](.env.example) para `backend/.env`. Em `ENV=dev` a `SECRET_KEY` de exemplo é aceita.
3. Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend && python main.py
```

4. Frontend (em outro terminal):

```bash
cd frontend-app
npm install
npm run dev
```

A UI fica em `http://localhost:5173` e o Vite faz proxy da API para `http://127.0.0.1:8000`.

### Docker

```bash
docker compose up --build
```

A aplicação sobe em `http://localhost:8000` (API + SPA buildada).

## Funcionalidades

- Cadastro, login JWT e papéis por obra (`owner`, `editor`, `membro`, `leitura`)
- Convites por link (7 dias)
- Atividades: criar, editar, excluir, filtrar e buscar
- Pagamentos por `atividade_id`, sem valor acima do restante
- Comprovante em disco, OCR em português e visualização autenticada
- Resumo agregado (`GET /obras/{id}/resumo`) com totais e **quem deve quanto** (cota igual do total)
- Gráficos e exportação PDF/Excel

Redefinição de senha pela API responde **503** até haver envio de e-mail.

## Testes

Os testes de API usam o MySQL configurado no `.env`.

```bash
pytest
```

Cobre login, 401/403 de papéis, pagamento próprio vs alheio, convite expirado/usado e o resumo de saldos.

## Estrutura

```
frontend-app/     SPA React (Vite + Tailwind)
backend/          FastAPI (rotas, auth, managers, OCR)
docker/           SQL inicial do MySQL
docker-compose.yml
requirements.txt  Dependências Python pinadas
```

## Variáveis de ambiente

Ver [`.env.example`](.env.example). `SECRET_KEY` é obrigatória. Fora de `ENV=dev`, chaves fracas conhecidas impedem a subida da API.

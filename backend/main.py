from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status

from config import logger
from models import (
    Activity, PendingActivity, PaidActivity, PaymentData, ExtractedData,
    UserPublic, RegisterRequest, ObraCreate, ObraOut, ConviteCreate, MembroUpdate, MembroOut, ValorMembro,
)
from models import PasswordResetRequest, PasswordResetResponse, PasswordUpdateRequest, PasswordUpdateResponse
from database import get_db_connection, initialize_database
from utils.ocr import ComprovanteReader, processar_comprovante_ocr
from managers.comprovante import ComprovantesManager
from managers.obra import ObrasManager
from auth.auth_user import (
    login_for_access_token, get_current_user, require_obra_member,
    generate_reset_token, reset_password, register_user,
)
from utils.cache import clear_cache

app = FastAPI(title="API de Gerenciamento de Despesas de Construção")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ComprovantesManager()
obras_manager = ObrasManager()


@app.on_event("startup")
async def startup_event():
    logger.info("Inicializando recursos da aplicação...")
    initialize_database()
    logger.info("Aplicação iniciada com sucesso")

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend-app", "dist"))


def wants_html(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    json_pos = accept.find("application/json")
    html_pos = accept.find("text/html")
    if html_pos == -1:
        return False
    if json_pos == -1:
        return True
    return html_pos < json_pos


def spa_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=404, detail="Frontend não encontrado. Execute npm run build em frontend-app.")
    return FileResponse(index_path)


@app.middleware("http")
async def spa_html_middleware(request: Request, call_next):
    if request.method in ("GET", "HEAD") and wants_html(request):
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json") or path.startswith("/docs") or path.startswith("/assets"):
            return await call_next(request)
        file_path = os.path.join(FRONTEND_DIR, path.lstrip("/"))
        if path != "/" and os.path.isfile(file_path):
            return FileResponse(file_path)
        if os.path.isfile(os.path.join(FRONTEND_DIR, "index.html")):
            return spa_index()
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def read_root():
    return spa_index()


@app.head("/")
def head_root():
    return {"message": "API de Gerenciamento de Despesas de Construção"}


@app.get("/health")
def health_check():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Verificação de saúde falhou: {e}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.head("/health")
def head_health_check():
    return {"status": "healthy"}


@app.post("/register", response_model=UserPublic)
def register(payload: RegisterRequest):
    return register_user(payload)


@app.get("/obras", response_model=List[ObraOut])
def list_obras(current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.listar_minhas_obras(current_user.id)


@app.post("/obras", response_model=ObraOut)
def create_obra(payload: ObraCreate, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.criar_obra(current_user.id, payload.nome, payload.descricao)


@app.get("/obras/{obra_id}", response_model=ObraOut)
def get_obra(obra_id: int, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.obter_obra(obra_id, current_user.id)


@app.get("/obras/{obra_id}/membros", response_model=List[MembroOut])
def list_membros(obra_id: int, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.listar_membros(obra_id, current_user.id)


@app.post("/obras/{obra_id}/convites")
def create_invite(obra_id: int, payload: ConviteCreate, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.criar_convite(obra_id, current_user.id, payload.papel, payload.email)


@app.patch("/obras/{obra_id}/membros/{membro_id}")
def update_membro(obra_id: int, membro_id: int, payload: MembroUpdate, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.atualizar_papel(obra_id, current_user.id, membro_id, payload.papel)


@app.delete("/obras/{obra_id}/membros/{membro_id}")
def delete_membro(obra_id: int, membro_id: int, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.remover_membro(obra_id, current_user.id, membro_id)


@app.get("/convite/{token}")
def get_invite(token: str):
    return obras_manager.obter_convite(token)


@app.post("/convite/{token}/aceitar")
def accept_invite(token: str, current_user: UserPublic = Depends(get_current_user)):
    return obras_manager.aceitar_convite(token, current_user.id)


@app.get("/atividades", response_model=List[Activity])
def get_activities(ctx: dict = Depends(require_obra_member("leitura"))):
    try:
        return manager.listar_atividades(ctx["obra_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar atividades: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades: {str(e)}")


@app.get("/atividades-pendentes", response_model=List[PendingActivity])
def get_pending_activities(ctx: dict = Depends(require_obra_member("leitura"))):
    try:
        return manager.listar_atividades_pendentes(ctx["obra_id"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades pendentes: {str(e)}")


@app.get("/atividades-pagas", response_model=List[PaidActivity])
def get_paid_activities(ctx: dict = Depends(require_obra_member("leitura"))):
    try:
        return manager.listar_atividades_pagas(ctx["obra_id"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar atividades pagas: {str(e)}")


@app.post("/update-status")
def update_status(ctx: dict = Depends(require_obra_member("editor"))):
    try:
        clear_cache("activities")
        return manager.atualizar_status(ctx["obra_id"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")


@app.post("/add-activity")
def add_activity(
    atividade: str = Form(...),
    valor: str = Form(...),
    setor: str = Form(...),
    data: str = Form(...),
    ctx: dict = Depends(require_obra_member("editor")),
):
    try:
        try:
            valor_float = float(valor.replace(',', '.'))
        except ValueError:
            raise HTTPException(status_code=400, detail="O valor deve ser um número")
        result = manager.adicionar_atividade(data, valor_float, setor, atividade, ctx["obra_id"])
        clear_cache("activities")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no endpoint /add-activity: {str(e)}")


@app.delete("/delete-activity/{id}")
def delete_activity(id: int, ctx: dict = Depends(require_obra_member("editor"))):
    try:
        result = manager.excluir_atividade(id, ctx["obra_id"])
        clear_cache("activities")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir atividade: {str(e)}")


@app.put("/edit-activity/{id}")
def edit_activity(
    id: int,
    atividade: str = Form(None),
    setor: str = Form(None),
    valor: str = Form(None),
    data: str = Form(None),
    ctx: dict = Depends(require_obra_member("editor")),
):
    try:
        valor_float = None
        if valor:
            try:
                valor_float = float(valor.replace(',', '.'))
            except ValueError:
                raise HTTPException(status_code=400, detail="O valor deve ser um número")
        result = manager.editar_atividade(
            id=id,
            obra_id=ctx["obra_id"],
            atividade=atividade if atividade else None,
            setor=setor if setor else None,
            valor=valor_float,
            data=data if data else None,
        )
        clear_cache("activities")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao editar atividade: {str(e)}")


@app.get("/valor-total")
def get_total_value(ctx: dict = Depends(require_obra_member("leitura"))):
    try:
        return {"total": manager.calcular_valor_total(ctx["obra_id"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total: {str(e)}")


@app.get("/valor-total-pago")
def get_valor_pago(ctx: dict = Depends(require_obra_member("leitura"))):
    try:
        return {"total_pago": manager.calcular_valor_total_pago(ctx["obra_id"])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular o valor total pago: {str(e)}")


@app.get("/valor-pago-membros", response_model=List[ValorMembro])
def get_valor_pago_membros(ctx: dict = Depends(require_obra_member("leitura"))):
    return manager.calcular_valor_pago_membros(ctx["obra_id"])


@app.post("/process-receipt", response_model=ExtractedData)
async def process_receipt(
    file: UploadFile = File(...),
    ctx: dict = Depends(require_obra_member("membro")),
):
    try:
        extension = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else 'jpg'
        contents = await file.read()
        texto_extraido = processar_comprovante_ocr(contents, filetype=extension)
        reader = ComprovanteReader()
        return ExtractedData(
            value=reader.extrair_valor(texto_extraido),
            date=reader.extrair_data(texto_extraido),
            name=reader.extrair_nome(texto_extraido),
            full_text=texto_extraido,
        )
    except Exception as e:
        logger.error(f"Erro ao processar o comprovante: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/register-payment")
async def register_payment(payment: PaymentData, ctx: dict = Depends(require_obra_member("membro"))):
    try:
        if not payment.activity or not payment.usuario_id or not payment.value:
            raise HTTPException(status_code=400, detail="Campos obrigatórios faltando")

        papel = ctx["papel"]
        if papel == "membro" and payment.usuario_id != ctx["user"].id:
            raise HTTPException(status_code=403, detail="Você só pode registrar o próprio pagamento")

        result = manager.preencher_pagamento(
            payment.value,
            payment.activity,
            payment.usuario_id,
            ctx["obra_id"],
            payment.sector,
            payment.date,
        )
        clear_cache("activities")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar pagamento: {str(e)}")


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await login_for_access_token(form_data)


@app.post("/password/request-reset", response_model=PasswordResetResponse)
async def request_password_reset(request: PasswordResetRequest):
    try:
        return generate_reset_token(request.username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar solicitação de redefinição de senha",
        )


@app.post("/password/reset", response_model=PasswordUpdateResponse)
async def confirm_password_reset(request: PasswordUpdateRequest):
    try:
        return await reset_password(request.username, request.reset_token, request.new_password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar redefinição de senha",
        )


assets_dir = os.path.join(FRONTEND_DIR, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

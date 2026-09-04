from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import secrets
import string

from database import get_db_connection
from models import User, UserPublic, PasswordResetResponse, PasswordUpdateResponse, RegisterRequest
from auth.passwords import hash_password, verify_password, is_hashed

logger = logging.getLogger("auth_user")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_padrao_para_desenvolvimento")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
PASSWORD_RESET_EXPIRE_MINUTES = 15

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
reset_tokens: Dict[str, Dict] = {}

ROLE_RANK = {
    "leitura": 1,
    "membro": 2,
    "editor": 3,
    "owner": 4,
}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


def _user_from_row(user_data: dict) -> User:
    return User(
        id=user_data["id"],
        nome=user_data["nome"],
        password=user_data["password"],
        status=user_data.get("status"),
    )


def to_public_user(user: User) -> UserPublic:
    return UserPublic(id=user.id, nome=user.nome)


def get_user_by_name(username: str) -> Optional[User]:
    """Busca usuário no DB pelo nome"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE LOWER(nome) = LOWER(%s)", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data:
            return _user_from_row(user_data)
        return None
    except Exception:
        return None


def get_user_by_id(user_id: int) -> Optional[User]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        if user_data:
            return _user_from_row(user_data)
        return None
    except Exception:
        return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    logger.info(f"Tentando autenticar usuário: {username}")
    user = get_user_by_name(username)
    if user is None:
        logger.warning(f"Usuário não encontrado: {username}")
        return None

    if is_hashed(user.password):
        if not verify_password(password, user.password):
            logger.warning(f"Senha incorreta para usuário {username}")
            return None
    else:
        if password != user.password:
            logger.warning(f"Senha incorreta para usuário {username}")
            return None

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPublic:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id = payload.get("user_id")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = get_user_by_name(token_data.username)
    if user is None:
        raise credentials_exception
    return to_public_user(user)


async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.nome, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=to_public_user(user),
    )


def register_user(payload: RegisterRequest) -> UserPublic:
    nome = (payload.nome or "").strip()
    password = payload.password or ""
    if not nome or not password:
        raise HTTPException(status_code=400, detail="E-mail e senha são obrigatórios")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 4 caracteres")

    if get_user_by_name(nome):
        raise HTTPException(status_code=400, detail="Já existe uma conta com este e-mail")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, password, status) VALUES (%s, %s, %s)",
        (nome, hash_password(password), "USER"),
    )
    user_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return UserPublic(id=user_id, nome=nome)


def get_membership(obra_id: int, usuario_id: int) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT om.papel, o.nome as obra_nome, o.criado_por, o.descricao
        FROM obra_membros om
        JOIN obras o ON o.id = om.obra_id
        WHERE om.obra_id = %s AND om.usuario_id = %s
        """,
        (obra_id, usuario_id),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def assert_obra_access(obra_id: int, usuario_id: int, min_papel: str = "leitura") -> dict:
    membership = get_membership(obra_id, usuario_id)
    if not membership:
        raise HTTPException(status_code=403, detail="Você não faz parte desta obra")
    if ROLE_RANK.get(membership["papel"], 0) < ROLE_RANK.get(min_papel, 99):
        raise HTTPException(status_code=403, detail="Você não tem permissão para esta ação")
    return membership


def require_obra_member(min_papel: str = "leitura"):
    def dependency(
        obra_id: int = Query(..., description="ID da obra"),
        current_user: UserPublic = Depends(get_current_user),
    ) -> dict:
        membership = assert_obra_access(obra_id, current_user.id, min_papel)
        return {
            "user": current_user,
            "obra_id": obra_id,
            "papel": membership["papel"],
            "membership": membership,
        }
    return dependency


def generate_reset_token(username: str) -> PasswordResetResponse:
    user = get_user_by_name(username)
    if not user:
        return PasswordResetResponse(
            success=True,
            message="Se o usuário existir, instruções foram enviadas.",
        )

    token_chars = string.ascii_letters + string.digits
    reset_token = ''.join(secrets.choice(token_chars) for _ in range(32))
    expires = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    reset_tokens[username] = {"token": reset_token, "expires": expires}

    return PasswordResetResponse(
        success=True,
        message=f"Token de recuperação: {reset_token}",
    )


def validate_reset_token(username: str, token: str) -> bool:
    if username not in reset_tokens:
        return False
    token_data = reset_tokens[username]
    if datetime.utcnow() > token_data["expires"]:
        del reset_tokens[username]
        return False
    return token_data["token"] == token


def update_password(username: str, new_password: str) -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET password = %s WHERE LOWER(nome) = LOWER(%s)",
            (hash_password(new_password), username),
        )
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return affected_rows > 0
    except Exception as e:
        logger.error(f"Erro ao atualizar senha: {str(e)}")
        return False


async def reset_password(username: str, reset_token: str, new_password: str) -> PasswordUpdateResponse:
    if not validate_reset_token(username, reset_token):
        return PasswordUpdateResponse(success=False, message="Token inválido ou expirado")

    if update_password(username, new_password):
        if username in reset_tokens:
            del reset_tokens[username]
        return PasswordUpdateResponse(success=True, message="Senha atualizada com sucesso")
    return PasswordUpdateResponse(success=False, message="Erro ao atualizar senha")

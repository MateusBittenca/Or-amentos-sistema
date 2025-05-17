from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from database import get_db_connection
from models import User

# Carrega variáveis de ambiente
load_dotenv()

# Configurações de segurança simplificadas
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_padrao_para_desenvolvimento")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 esquema para autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class TokenData(BaseModel):
    username: Optional[str] = None


# Funções de banco de dados
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
            return User(**user_data)
        return None
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None


# Autenticação e tokens
def authenticate_user(username: str, password: str) -> Optional[User]:
    """Autenticação simplificada por nome e senha"""
    user = get_user_by_name(username)
    
    # Verifica se o usuário existe e se a senha está correta
    if not user or password != user.password:
        return None
        
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Dependências do FastAPI
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Valida token e retorna o usuário"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user_by_name(token_data.username)
    if user is None:
        raise credentials_exception
    return user


# Endpoint de login
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Endpoint de login para gerar token usando apenas nome e senha"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Simplificado: sem verificação de status do usuário

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Armazena o nome do usuário no token em vez do ID
    access_token = create_access_token(
        data={"sub": user.nome},  # Usando o nome do usuário como identificador
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer", user=user)
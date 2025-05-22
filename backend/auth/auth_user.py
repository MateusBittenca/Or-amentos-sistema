from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging

from database import get_db_connection
from models import User

# Configurar logging
logger = logging.getLogger("auth_user")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Carrega variáveis de ambiente
load_dotenv()

# Configurações de segurança
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
        return None


# Autenticação e tokens
def authenticate_user(username: str, password: str) -> Optional[User]:
    """Autenticação simplificada por nome e senha"""
    logger.info(f"Tentando autenticar usuário: {username}")
    user = get_user_by_name(username)
    

    
    # Verifica se a senha está correta
    if password != user.password:
        logger.warning(f"Senha incorreta para usuário {username}")
        return None
    
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise


# Dependências do FastAPI
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Valida token e retorna o usuário"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodifica o token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extrai o nome de usuário
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username)
        
    except JWTError as e:
        raise credentials_exception
    except Exception as e:
        raise credentials_exception

    # Busca o usuário no banco de dados
    user = get_user_by_name(token_data.username)
    
    if user is None:
        raise credentials_exception
        
    return user


# Endpoint de login
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Endpoint de login para gerar token usando apenas nome e senha"""

    # Autentica o usuário
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gera o token de acesso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    try:
        # Armazena o nome do usuário no token em vez do ID
        access_token = create_access_token(
            data={"sub": user.nome},  # Usando o nome do usuário como identificador
            expires_delta=access_token_expires
        )
        
        # Retorna o token
        response = Token(access_token=access_token, token_type="bearer", user=user)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao gerar token de acesso",
        )


# Função auxiliar para verificação simplificada de autenticação
# Útil para endpoints onde não precisamos usar os dados do usuário
def require_auth(token: str = Depends(oauth2_scheme)):
    """Função auxiliar que apenas verifica se o usuário está autenticado"""
    # Isso vai verificar o token e levantar exceção se inválido
    get_current_user(token)
    return True
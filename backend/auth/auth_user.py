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

logger.info(f"SECRET_KEY carregada: {'*' * len(SECRET_KEY)}")
logger.info(f"Usando algoritmo: {ALGORITHM}")
logger.info(f"Tempo de expiração de token configurado para: {ACCESS_TOKEN_EXPIRE_MINUTES} minutos")

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
    logger.debug(f"Buscando usuário pelo nome: {username}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE LOWER(nome) = LOWER(%s)", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if user_data:
            logger.debug(f"Usuário encontrado: {username}")
            return User(**user_data)
        
        logger.warning(f"Usuário não encontrado: {username}")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}", exc_info=True)
        return None


# Autenticação e tokens
def authenticate_user(username: str, password: str) -> Optional[User]:
    """Autenticação simplificada por nome e senha"""
    logger.info(f"Tentando autenticar usuário: {username}")
    user = get_user_by_name(username)
    
    if not user:
        logger.warning(f"Usuário {username} não encontrado no banco de dados")
        return None
    
    # Verifica se a senha está correta
    if password != user.password:
        logger.warning(f"Senha incorreta para usuário {username}")
        return None
    
    logger.info(f"Usuário {username} autenticado com sucesso")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT token"""
    logger.debug(f"Criando access token para dados: {data}")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    logger.debug(f"Token expira em: {expire}")
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Token JWT gerado com sucesso: {encoded_jwt[:10]}...")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Erro ao gerar token JWT: {e}", exc_info=True)
        raise


# Dependências do FastAPI
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Valida token e retorna o usuário"""
    logger.debug(f"Validando token: {token[:10]}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodifica o token
        logger.debug("Tentando decodificar token JWT")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Token decodificado com sucesso. Payload: {payload}")
        
        # Extrai o nome de usuário
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token não contém campo 'sub' (nome de usuário)")
            raise credentials_exception
            
        token_data = TokenData(username=username)
        logger.debug(f"Token contém username: {username}")
        
    except JWTError as e:
        logger.error(f"Erro ao decodificar JWT: {e}", exc_info=True)
        raise credentials_exception
    except Exception as e:
        logger.error(f"Erro inesperado ao processar token: {e}", exc_info=True)
        raise credentials_exception

    # Busca o usuário no banco de dados
    logger.debug(f"Buscando usuário do token: {token_data.username}")
    user = get_user_by_name(token_data.username)
    
    if user is None:
        logger.warning(f"Usuário {token_data.username} não encontrado no banco")
        raise credentials_exception
        
    logger.info(f"Usuário autenticado com sucesso: {user.nome}")
    return user


# Endpoint de login
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """Endpoint de login para gerar token usando apenas nome e senha"""
    logger.info(f"Tentativa de login para usuário: {form_data.username}")
    
    # Autentica o usuário
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Falha na autenticação para usuário: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gera o token de acesso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    logger.debug(f"Criando token para usuário {user.nome} com expiração de {ACCESS_TOKEN_EXPIRE_MINUTES} minutos")
    
    try:
        # Armazena o nome do usuário no token em vez do ID
        access_token = create_access_token(
            data={"sub": user.nome},  # Usando o nome do usuário como identificador
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token gerado com sucesso para usuário {user.nome}: {access_token[:10]}...")
        
        # Retorna o token
        response = Token(access_token=access_token, token_type="bearer", user=user)
        return response
    except Exception as e:
        logger.error(f"Erro ao gerar token de acesso: {e}", exc_info=True)
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
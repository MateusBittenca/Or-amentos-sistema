from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import secrets
import string

from database import get_db_connection
from models import User, PasswordResetResponse, PasswordUpdateResponse

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
PASSWORD_RESET_EXPIRE_MINUTES = 15

# OAuth2 esquema para autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Armazenamento temporário de tokens de reset (em produção, use banco de dados)
reset_tokens: Dict[str, Dict] = {}


# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User
    status: str  # Adding status field to the token response


class TokenData(BaseModel):
    username: Optional[str] = None
    status: Optional[str] = None  # Adding status field to token data

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
    
    # Verifica se o usuário existe
    if user is None:
        logger.warning(f"Usuário não encontrado: {username}")
        return None
    
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
            
        # Extrai o status (se disponível)
        status: str = payload.get("status")
        
        token_data = TokenData(username=username, status=status)
        
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
        # Armazena o nome do usuário e status no token
        access_token = create_access_token(
            data={
                "sub": user.nome,  # Usando o nome do usuário como identificador
                "status": user.status  # Incluindo o status do usuário no token
            },
            expires_delta=access_token_expires
        )
        
        # Retorna o token
        response = Token(
            access_token=access_token, 
            token_type="bearer", 
            user=user,
            status=user.status  # Incluindo o status na resposta
        )
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

# Funções para recuperação de senha

def generate_reset_token(username: str) -> PasswordResetResponse:
    """
    Gera um token de recuperação de senha para o usuário
    """
    user = get_user_by_name(username)
    if not user:
        logger.warning(f"Tentativa de recuperação de senha para usuário inexistente: {username}")
        # Retornamos sucesso mesmo se o usuário não existe para evitar enumeration attacks
        return PasswordResetResponse(
            success=True,
            message="Se o usuário existir, instruções foram enviadas."
        )
    
    # Gerar token aleatório
    token_chars = string.ascii_letters + string.digits
    reset_token = ''.join(secrets.choice(token_chars) for _ in range(32))
    
    # Armazenar token com informações de expiração
    expires = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    reset_tokens[username] = {
        "token": reset_token,
        "expires": expires
    }
    
    logger.info(f"Token de recuperação gerado para {username}: {reset_token}")
    
    # Em um ambiente de produção, enviaríamos um email aqui
    # Por enquanto, apenas retornamos o token para simular
    return PasswordResetResponse(
        success=True,
        message=f"Token de recuperação: {reset_token}"
    )

def validate_reset_token(username: str, token: str) -> bool:
    """
    Valida se o token de recuperação é válido para o usuário
    """
    if username not in reset_tokens:
        logger.warning(f"Token não encontrado para usuário: {username}")
        return False
    
    token_data = reset_tokens[username]
    
    # Verificar expiração
    if datetime.utcnow() > token_data["expires"]:
        logger.warning(f"Token expirado para usuário: {username}")
        # Limpar token expirado
        del reset_tokens[username]
        return False
    
    # Verificar token
    if token_data["token"] != token:
        logger.warning(f"Token inválido para usuário: {username}")
        return False
    
    return True

def update_password(username: str, new_password: str) -> bool:
    """
    Atualiza a senha do usuário no banco de dados
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Atualizar senha
        cursor.execute(
            "UPDATE usuarios SET password = %s WHERE LOWER(nome) = LOWER(%s)",
            (new_password, username)
        )
        
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logger.info(f"Senha atualizada com sucesso para usuário: {username}")
            return True
        else:
            logger.warning(f"Usuário não encontrado ao atualizar senha: {username}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao atualizar senha: {str(e)}")
        return False

async def reset_password(username: str, reset_token: str, new_password: str) -> PasswordUpdateResponse:
    """
    Redefine a senha do usuário usando o token de recuperação
    """
    # Validar token
    if not validate_reset_token(username, reset_token):
        return PasswordUpdateResponse(
            success=False,
            message="Token inválido ou expirado"
        )
    
    # Atualizar senha
    if update_password(username, new_password):
        # Limpar token após uso bem-sucedido
        if username in reset_tokens:
            del reset_tokens[username]
            
        return PasswordUpdateResponse(
            success=True,
            message="Senha atualizada com sucesso"
        )
    else:
        return PasswordUpdateResponse(
            success=False,
            message="Erro ao atualizar senha"
        )
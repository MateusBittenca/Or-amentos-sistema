import time
from typing import Dict, Any, Tuple, Optional, Callable
from functools import wraps
from config import logger

# Cache com timeout para resultados de consultas
cache_store: Dict[str, Tuple[Any, float]] = {}
cache_expiry = 30  # 30 segundos como padrão


def get_cached_data(key: str) -> Optional[Any]:
    """Obter dados do cache se válidos"""
    if key in cache_store:
        data, timestamp = cache_store[key]
        if time.time() - timestamp < cache_expiry:
            return data
        else:
            # Expirado, remover do cache
            del cache_store[key]
    return None


def set_cached_data(key: str, data: Any, expiry: int = None) -> None:
    """Armazenar dados no cache com timestamp atual"""
    cache_store[key] = (data, time.time())


def clear_cache(prefix: str = None) -> None:
    """Limpar todo o cache ou apenas entradas com um prefixo específico"""
    global cache_store
    if prefix:
        keys_to_delete = [k for k in cache_store.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del cache_store[key]
    else:
        cache_store = {}
    logger.debug(f"Cache {'com prefixo '+prefix if prefix else 'completo'} limpo")


def cached(expiry: int = None, key_prefix: str = ""):
    """
    Decorador para funções que precisam de cache
    
    Args:
        expiry: Tempo de expiração em segundos
        key_prefix: Prefixo opcional para a chave
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Criar chave baseada na função, argumentos e prefixo
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Verificar cache antes de executar
            cached_result = get_cached_data(cache_key)
            if cached_result is not None:
                logger.debug(f"Usando dados em cache para {cache_key}")
                return cached_result
                
            # Executar função
            result = await func(*args, **kwargs)
            
            # Armazenar resultado no cache
            set_cached_data(cache_key, result, expiry)
            logger.debug(f"Armazenado resultado em cache para {cache_key}")
            
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Criar chave baseada na função, argumentos e prefixo
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Verificar cache antes de executar
            cached_result = get_cached_data(cache_key)
            if cached_result is not None:
                logger.debug(f"Usando dados em cache para {cache_key}")
                return cached_result
                
            # Executar função
            result = func(*args, **kwargs)
            
            # Armazenar resultado no cache
            set_cached_data(cache_key, result, expiry)
            logger.debug(f"Armazenado resultado em cache para {cache_key}")
            
            return result
            
        if asyncio_based_function(func):
            return async_wrapper
        return sync_wrapper
            
    return decorator


def asyncio_based_function(func):
    """Verificar se uma função é baseada em asyncio"""
    import inspect
    return inspect.iscoroutinefunction(func) 
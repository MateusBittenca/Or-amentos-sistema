import io
import uuid
from pathlib import Path
from fastapi import HTTPException
from PIL import Image
from config import MAX_RECEIPT_BYTES, UPLOADS_DIR

ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def validate_receipt_bytes(contents: bytes) -> str:
    if not contents:
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    if len(contents) > MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=400, detail="O comprovante deve ter no máximo 5 MB")
    try:
        image = Image.open(io.BytesIO(contents))
        fmt = (image.format or "").upper()
        image.verify()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Envie uma imagem JPG, PNG ou WebP")
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Envie uma imagem JPG, PNG ou WebP")
    return ALLOWED_FORMATS[fmt]


def save_receipt(obra_id: int, contents: bytes, extension: str) -> str:
    dest_dir = UPLOADS_DIR / str(obra_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{extension}"
    path = dest_dir / name
    path.write_bytes(contents)
    return f"{obra_id}/{name}"


def receipt_abs_path(relative: str) -> Path:
    uploads_root = UPLOADS_DIR.resolve()
    path = (UPLOADS_DIR / relative).resolve()
    if uploads_root not in path.parents and path != uploads_root:
        raise HTTPException(status_code=404, detail="Comprovante não encontrado")
    return path

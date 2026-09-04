from pydantic import BaseModel
from typing import List, Optional


class PaymentItem(BaseModel):
    usuario_id: int
    nome: str
    valor: float


class Activity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    value: float
    date: Optional[str] = None
    total_pago: float = 0
    valor_restante: float = 0
    pagamentos: List[PaymentItem] = []
    status: Optional[str] = None


class User(BaseModel):
    id: int
    nome: str
    password: str
    status: Optional[str] = None


class UserPublic(BaseModel):
    id: int
    nome: str


class RegisterRequest(BaseModel):
    nome: str
    password: str


class PendingActivity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    total_value: float
    valor_restante: float
    date: Optional[str] = None
    total_pago: float = 0
    pagamentos: List[PaymentItem] = []


class PaidActivity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    total_value: float
    date: Optional[str] = None
    total_pago: float = 0
    pagamentos: List[PaymentItem] = []
    status: str


class PaymentData(BaseModel):
    activity: str
    sector: Optional[str] = None
    usuario_id: int
    value: str
    date: Optional[str] = None


class ExtractedData(BaseModel):
    value: Optional[str] = None
    date: Optional[str] = None
    name: Optional[str] = None
    full_text: Optional[str] = None


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetResponse(BaseModel):
    message: str
    success: bool


class PasswordUpdateRequest(BaseModel):
    username: str
    reset_token: str
    new_password: str


class PasswordUpdateResponse(BaseModel):
    success: bool
    message: str


class ObraCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None


class ObraOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    papel: str
    criado_por: int


class ConviteCreate(BaseModel):
    papel: str = "membro"
    email: Optional[str] = None


class MembroUpdate(BaseModel):
    papel: str


class MembroOut(BaseModel):
    usuario_id: int
    nome: str
    papel: str


class ValorMembro(BaseModel):
    usuario_id: int
    nome: str
    total: float

from pydantic import BaseModel
from typing import List, Optional


class PaymentItem(BaseModel):
    id: int
    usuario_id: int
    nome: str
    valor: float
    comprovante_url: Optional[str] = None


class ParticipacaoAtividade(BaseModel):
    usuario_id: int
    nome: str
    percentual: float


class Activity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    value: float
    date: Optional[str] = None
    total_pago: float = 0
    valor_restante: float = 0
    pagamentos: List[PaymentItem] = []
    participacao: List[ParticipacaoAtividade] = []
    status: Optional[str] = None


class User(BaseModel):
    id: int
    nome: str
    password: str
    status: Optional[str] = None
    nome_exibicao: Optional[str] = None


class UserPublic(BaseModel):
    id: int
    nome: str


class RegisterRequest(BaseModel):
    nome: str
    password: str
    nome_exibicao: str


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
    atividade_id: int
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
    participacao: Optional[float] = None


class ParticipacaoItem(BaseModel):
    usuario_id: int
    percentual: float


class ParticipacaoObraUpdate(BaseModel):
    participantes: List[ParticipacaoItem]


class Transferencia(BaseModel):
    de_usuario_id: int
    de_nome: str
    para_usuario_id: int
    para_nome: str
    valor: float


class ValorMembro(BaseModel):
    usuario_id: int
    nome: str
    total: float


class SaldoMembro(BaseModel):
    usuario_id: int
    nome: str
    pago: float
    parte: float
    saldo: float


class ResumoObra(BaseModel):
    total: float
    total_pago: float
    restante: float
    membros: List[ValorMembro]
    saldos: List[SaldoMembro]
    transferencias: List[Transferencia] = []
    atividades: List[Activity]

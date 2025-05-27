from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union

class Activity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    value: float
    date: Optional[str] = None
    diego_ana: Optional[float] = None
    alex_rute: Optional[float] = None
    status: Optional[str] = None

class User(BaseModel):
    id: int
    nome: str
    password: str
    status: str

    
class PendingActivity(BaseModel):
    id: int  
    activity: str
    sector: Optional[str] = None
    total_value: float
    valor_restante: float
    date: Optional[str] = None
    diego_ana: float
    alex_rute: float

class PaidActivity(BaseModel):
    id: int
    activity: str
    sector: Optional[str] = None
    total_value: float
    date: Optional[str] = None
    diego_ana: float
    alex_rute: float
    status: str
    
class PaymentData(BaseModel):
    activity: str
    sector: Optional[str] = None
    payer: str
    value: str
    date: Optional[str] = None

class ExtractedData(BaseModel):
    value: Optional[str] = None
    date: Optional[str] = None
    name: Optional[str] = None
    full_text: Optional[str] = None

# Password reset models
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
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class UsuarioRegistro(BaseModel):
    username: str
    email: str
    password: str
    telefono: Optional[str] = None

class UsuarioLogin(BaseModel):
    username: str
    password: str

class LecturaCreate(BaseModel):
    nitrogeno: float
    fosforo: float
    potasio: float
    ph: float
    humedad: float
    temperatura: float
    luz_solar: float

class UsuarioResponse(BaseModel):
    id: int
    username: str
    email: str
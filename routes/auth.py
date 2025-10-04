'''
from fastapi import APIRouter, HTTPException
from models import UsuarioRegistro, UsuarioLogin
from database import get_db_connection

router = APIRouter(prefix="/api", tags=["auth"])

@router.post("/registro")
async def registrar_usuario(usuario: UsuarioRegistro):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si usuario existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = %s OR email = %s", 
                      usuario.username, usuario.email)
        count = cursor.fetchone()[0]
        
        if count > 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Usuario o email ya existe")
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (username, email, password, telefono) 
            VALUES (?, ?, ?, ?)
        """, usuario.username, usuario.email, usuario.password, usuario.telefono)
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Usuario registrado"}
        
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/login")
async def login_usuario(usuario: UsuarioLogin):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email FROM usuarios 
            WHERE (username = %s OR email = %s) AND password = %s
        """, usuario.username, usuario.username, usuario.password)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "success": True,
                "usuario": {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2]
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    '''

from fastapi import APIRouter, HTTPException
from models import UsuarioRegistro, UsuarioLogin
from database import get_db_connection

router = APIRouter(prefix="/api", tags=["auth"])

@router.post("/registro")
async def registrar_usuario(usuario: UsuarioRegistro):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si usuario existe
        cursor.execute(
            "SELECT COUNT(*) FROM usuarios WHERE username = %s OR email = %s", 
            (usuario.username, usuario.email)
        )
        count = cursor.fetchone()[0]
        
        if count > 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Usuario o email ya existe")
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (username, email, password, telefono) 
            VALUES (%s, %s, %s, %s)
        """, (usuario.username, usuario.email, usuario.password, usuario.telefono))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Usuario registrado"}
        
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/login")
async def login_usuario(usuario: UsuarioLogin):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email FROM usuarios 
            WHERE (username = %s OR email = %s) AND password = %s
        """, (usuario.username, usuario.username, usuario.password))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "success": True,
                "usuario": {
                    "id": result[0],
                    "username": result[1],
                    "email": result[2]
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

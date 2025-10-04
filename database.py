import pymssql
from fastapi import HTTPException

def get_db_connection():
    try:
        conn = pymssql.connect(
            server="DBAGROMAGU.mssql.somee.com",
            user="pmacajol_SQLLogin_1",
            password="wf1fecsxmw",
            database="DBAGROMAGU",
            port=1433,
            login_timeout=10
        )
        # Importante: cursor normal (igual que pyodbc)
        conn.cursor()
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error de conexión a la base de datos: {str(e)}")

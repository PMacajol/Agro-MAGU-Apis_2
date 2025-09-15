
import pyodbc
from fastapi import HTTPException

def get_db_connection():
    try:
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=DBAGROMAGU.mssql.somee.com;"
            "DATABASE=DBAGROMAGU;"
            "UID=pmacajol_SQLLogin_1;"
            "PWD=wf1fecsxmw;"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(connection_string, timeout=10)
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error de conexión a la base de datos: {str(e)}")

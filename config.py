"""
import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DBAGROMAGU.mssql.somee.com;"
    "DATABASE=DBAGROMAGU;"
    "UID=pmacajol_SQLLogin_1;"
    "PWD=wf1fecsxmw;"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 username FROM USUARIOS")
    row = cursor.fetchone()
    print("Conexión OK. Usuario encontrado:", row[0])
except Exception as e:
    print("Error de conexión:", e)

"""
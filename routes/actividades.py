from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection
from datetime import datetime

router = APIRouter(prefix="/api/actividades", tags=["actividades"])

# ----------------- MODELOS -----------------
class ActividadUpdate(BaseModel):
    titulo: str
    fecha: str  # formato "YYYY-MM-DD"
    completada: bool

class ActividadCreate(BaseModel):
    usuario_id: int
    titulo: str
    fecha: str  # formato "YYYY-MM-DD"
    completada: bool = False

# ----------------- ENDPOINTS EXISTENTES -----------------
@router.get("/{usuario_id}/{mes}/{anio}")
async def obtener_actividades(usuario_id: int, mes: int, anio: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        fecha_inicio = datetime(anio, mes, 1)
        fecha_fin = datetime(anio + 1, 1, 1) if mes == 12 else datetime(anio, mes + 1, 1)

        cursor.execute("""
            SELECT id, fecha, titulo, completada
            FROM actividades
            WHERE usuario_id = ?
            AND fecha >= ? AND fecha < ?
            ORDER BY fecha
        """, (usuario_id, fecha_inicio, fecha_fin))

        results = cursor.fetchall()
        conn.close()

        actividades = [
            {
                "id": row[0],
                "fecha": row[1].strftime("%Y-%m-%d"),
                "titulo": row[2],
                "completada": bool(row[3])
            }
            for row in results
        ]

        return actividades

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{actividad_id}/completar")
async def completar_actividad(actividad_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE actividades SET completada = 1 WHERE id = ?", (actividad_id,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Actividad completada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{actividad_id}")
async def modificar_actividad(actividad_id: int, datos: ActividadUpdate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        fecha_dt = datetime.strptime(datos.fecha, "%Y-%m-%d")
        cursor.execute("""
            UPDATE actividades
            SET titulo = ?, fecha = ?, completada = ?
            WHERE id = ?
        """, (datos.titulo, fecha_dt, int(datos.completada), actividad_id))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Actividad no encontrada")

        conn.commit()
        conn.close()
        return {"success": True, "message": "Actividad modificada"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- NUEVO: CREAR ACTIVIDAD -----------------
@router.post("/")
async def crear_actividad(datos: ActividadCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        fecha_dt = datetime.strptime(datos.fecha, "%Y-%m-%d")

        cursor.execute("""
            INSERT INTO actividades (usuario_id, titulo, fecha, completada)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?)
        """, (datos.usuario_id, datos.titulo, fecha_dt, int(datos.completada)))

        # Obtener el nuevo ID
        new_id = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        return {"success": True, "message": "Actividad creada", "id": new_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ----------------- NUEVO: ELIMINAR ACTIVIDAD -----------------
@router.delete("/{actividad_id}")
async def eliminar_actividad(actividad_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM actividades WHERE id = ?", (actividad_id,))
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Actividad no encontrada")

        conn.commit()
        conn.close()
        return {"success": True, "message": "Actividad eliminada"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- NUEVO: ACTIVIDAD DE HOY O LA SIGUIENTE -----------------
@router.get("/hoy/{usuario_id}")
async def actividad_hoy_o_siguiente(usuario_id: int):
    """
    Devuelve la actividad de hoy de un usuario. 
    Si no hay, devuelve la siguiente actividad pendiente.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hoy = datetime.today().date()

        # Buscar actividad de hoy
        cursor.execute("""
            SELECT TOP 1 id, fecha, titulo, completada
            FROM actividades
            WHERE usuario_id = ? AND CAST(fecha AS DATE) = ?
            ORDER BY fecha
        """, (usuario_id, hoy))
        actividad = cursor.fetchone()

        if actividad:
            conn.close()
            return {
                "id": actividad[0],
                "fecha": actividad[1].strftime("%Y-%m-%d"),
                "titulo": actividad[2],
                "completada": bool(actividad[3])
            }

        # Si no hay actividad hoy, buscar la siguiente pendiente
        cursor.execute("""
            SELECT TOP 1 id, fecha, titulo, completada
            FROM actividades
            WHERE usuario_id = ? AND CAST(fecha AS DATE) > ?
            ORDER BY fecha
        """, (usuario_id, hoy))
        siguiente = cursor.fetchone()
        conn.close()

        if siguiente:
            return {
                "id": siguiente[0],
                "fecha": siguiente[1].strftime("%Y-%m-%d"),
                "titulo": siguiente[2],
                "completada": bool(siguiente[3]),
                "mensaje": "No hay actividad hoy, esta es la siguiente programada"
            }

        return {"message": "No hay actividades para hoy ni próximas"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

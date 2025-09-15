from fastapi import APIRouter, HTTPException, Query
from models import LecturaCreate
from database import get_db_connection
from datetime import datetime

router = APIRouter(prefix="/api/lecturas", tags=["lecturas"])

# ----------------- CREAR LECTURA -----------------
@router.post("")
async def crear_lectura(lectura: LecturaCreate, usuario_id: int = Query(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO lecturas (usuario_id, nitrogeno, fosforo, potasio, ph, humedad, temperatura, luz_solar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, lectura.nitrogeno, lectura.fosforo, lectura.potasio, 
              lectura.ph, lectura.humedad, lectura.temperatura, lectura.luz_solar))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Lectura guardada"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- ÚLTIMA LECTURA -----------------
@router.get("/ultima/{usuario_id}")
async def obtener_ultima_lectura(usuario_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TOP 1 nitrogeno, fosforo, potasio, ph, humedad, temperatura, luz_solar, fecha_hora
            FROM lecturas 
            WHERE usuario_id = ? 
            ORDER BY fecha_hora DESC
        """, (usuario_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "nitrogeno": float(result[0]),
                "fosforo": float(result[1]),
                "potasio": float(result[2]),
                "ph": float(result[3]),
                "humedad": float(result[4]),
                "temperatura": float(result[5]),
                "luz_solar": float(result[6]),
                "fecha_hora": result[7].isoformat()
            }
        else:
            return {"message": "No hay lecturas disponibles"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- HISTÓRICO -----------------
@router.get("/historico/{usuario_id}/{periodo}")
async def obtener_datos_historicos(usuario_id: int, periodo: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if periodo == "1mes":
            fecha_consulta = "DATEADD(MONTH, -1, GETDATE())"
        elif periodo == "3meses":
            fecha_consulta = "DATEADD(MONTH, -3, GETDATE())"
        else:
            fecha_consulta = "DATEADD(MONTH, -6, GETDATE())"
        
        query = f"""
            SELECT 
                CAST(fecha_hora AS DATE) as fecha,
                AVG(CAST(nitrogeno AS FLOAT)) as nitrogeno,
                AVG(CAST(fosforo AS FLOAT)) as fosforo,
                AVG(CAST(potasio AS FLOAT)) as potasio,
                AVG(CAST(ph AS FLOAT)) as ph,
                AVG(CAST(humedad AS FLOAT)) as humedad,
                AVG(CAST(temperatura AS FLOAT)) as temperatura
            FROM lecturas 
            WHERE usuario_id = ? AND fecha_hora >= {fecha_consulta}
            GROUP BY CAST(fecha_hora AS DATE)
            ORDER BY CAST(fecha_hora AS DATE)
        """
        
        cursor.execute(query, (usuario_id,))
        results = cursor.fetchall()
        conn.close()
        
        datos = []
        for row in results:
            datos.append({
                "fecha": row[0].strftime("%Y-%m-%d"),
                "nitrogeno": float(row[1]) if row[1] else 0,
                "fosforo": float(row[2]) if row[2] else 0,
                "potasio": float(row[3]) if row[3] else 0,
                "ph": float(row[4]) if row[4] else 0,
                "humedad": float(row[5]) if row[5] else 0,
                "temperatura": float(row[6]) if row[6] else 0
            })
        
        return datos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- NUEVO: PROMEDIO DEL DÍA -----------------
@router.get("/promedio/{usuario_id}")
async def promedio_dia(usuario_id: int, fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD")):
    """
    Devuelve el promedio de todas las lecturas de un usuario en un día específico,
    redondeando los valores a 2 decimales.
    """
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_inicio = fecha_dt.strftime("%Y-%m-%d 00:00:00")
        fecha_fin = fecha_dt.strftime("%Y-%m-%d 23:59:59")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                AVG(CAST(nitrogeno AS FLOAT)) as nitrogeno,
                AVG(CAST(fosforo AS FLOAT)) as fosforo,
                AVG(CAST(potasio AS FLOAT)) as potasio,
                AVG(CAST(ph AS FLOAT)) as ph,
                AVG(CAST(humedad AS FLOAT)) as humedad,
                AVG(CAST(temperatura AS FLOAT)) as temperatura,
                AVG(CAST(luz_solar AS FLOAT)) as luz_solar
            FROM lecturas
            WHERE usuario_id = ? AND fecha_hora BETWEEN ? AND ?
        """, (usuario_id, fecha_inicio, fecha_fin))

        result = cursor.fetchone()
        conn.close()

        if result and any(result):
            return {
                "fecha": fecha,
                "nitrogeno": round(float(result[0]), 2) if result[0] else 0,
                "fosforo": round(float(result[1]), 2) if result[1] else 0,
                "potasio": round(float(result[2]), 2) if result[2] else 0,
                "ph": round(float(result[3]), 2) if result[3] else 0,
                "humedad": round(float(result[4]), 2) if result[4] else 0,
                "temperatura": round(float(result[5]), 2) if result[5] else 0,
                "luz_solar": round(float(result[6]), 2) if result[6] else 0
            }
        else:
            return {"message": "No hay lecturas para esa fecha"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ----------------- HISTÓRICO PARA GRÁFICAS -----------------
@router.get("/historico/{usuario_id}/{periodo}")
async def obtener_datos_historicos(usuario_id: int, periodo: str):
    """
    Devuelve el histórico dividido por parámetro con valor actual, valor anterior,
    descripción y datos completos para gráficas con formato de series temporales.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Definir fecha de consulta según período
        if periodo == "1mes":
            fecha_consulta = "DATEADD(MONTH, -1, GETDATE())"
            periodo_texto = "Último mes"
        elif periodo == "3meses":
            fecha_consulta = "DATEADD(MONTH, -3, GETDATE())"
            periodo_texto = "Últimos 3 meses"
        else:
            fecha_consulta = "DATEADD(MONTH, -6, GETDATE())"
            periodo_texto = "Últimos 6 meses"

        # Traer todas las lecturas agrupadas por fecha con formato para gráficas
        query = f"""
            SELECT 
                CAST(fecha_hora AS DATE) as fecha,
                AVG(CAST(nitrogeno AS FLOAT)) as nitrogeno,
                AVG(CAST(fosforo AS FLOAT)) as fosforo,
                AVG(CAST(potasio AS FLOAT)) as potasio,
                AVG(CAST(ph AS FLOAT)) as ph,
                AVG(CAST(humedad AS FLOAT)) as humedad,
                AVG(CAST(temperatura AS FLOAT)) as temperatura
            FROM lecturas 
            WHERE usuario_id = ? AND fecha_hora >= {fecha_consulta}
            GROUP BY CAST(fecha_hora AS DATE)
            ORDER BY CAST(fecha_hora AS DATE)
        """
        cursor.execute(query, (usuario_id,))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {"message": "No hay datos históricos disponibles"}

        # Procesar datos para formato de gráficas
        fechas = []
        datos_nitrogeno = []
        datos_fosforo = []
        datos_potasio = []
        datos_ph = []
        datos_humedad = []
        datos_temperatura = []

        for row in results:
            fecha_str = row[0].strftime("%Y-%m-%d")
            fechas.append(fecha_str)
            datos_nitrogeno.append(float(row[1]))
            datos_fosforo.append(float(row[2]))
            datos_potasio.append(float(row[3]))
            datos_ph.append(float(row[4]))
            datos_humedad.append(float(row[5]))
            datos_temperatura.append(float(row[6]))

        # Tomamos el último valor y el anterior para mostrar la comparación
        ultimo = results[-1]
        anterior = results[-2] if len(results) > 1 else ultimo

        # Calcular tendencias
        def calcular_tendencia(datos):
            if len(datos) < 2:
                return "estable"
            inicio = sum(datos[:len(datos)//3]) / (len(datos)//3)
            final = sum(datos[-len(datos)//3:]) / (len(datos)//3)
            if final > inicio * 1.05:  # 5% de incremento
                return "creciente"
            elif final < inicio * 0.95:  # 5% de decremento
                return "decreciente"
            else:
                return "estable"

        tendencias = {
            "nitrogeno": calcular_tendencia(datos_nitrogeno),
            "fosforo": calcular_tendencia(datos_fosforo),
            "potasio": calcular_tendencia(datos_potasio),
            "ph": calcular_tendencia(datos_ph),
            "humedad": calcular_tendencia(datos_humedad),
            "temperatura": calcular_tendencia(datos_temperatura)
        }

        # Generar recomendaciones basadas en tendencias
        recomendaciones = []
        tendencias_positivas = []

        for parametro, tendencia in tendencias.items():
            if tendencia == "creciente":
                if parametro == "nitrogeno":
                    tendencias_positivas.append("El nitrógeno ha aumentado consistentemente")
                elif parametro == "potasio":
                    tendencias_positivas.append("Los niveles de potasio se mantienen óptimos")
                elif parametro == "humedad":
                    tendencias_positivas.append("La humedad del suelo muestra mejora")
                elif parametro == "ph":
                    if datos_ph[-1] > 7.0:
                        recomendaciones.append("Monitorear el pH regularmente")
                    else:
                        tendencias_positivas.append("El pH se mantiene en niveles óptimos")
            elif tendencia == "decreciente":
                if parametro == "nitrogeno":
                    recomendaciones.append("Considerar aplicación de fertilizante nitrogenado")
                elif parametro == "fosforo":
                    recomendaciones.append("Evaluar necesidad de fósforo")
                elif parametro == "humedad":
                    recomendaciones.append("Ajustar riego según la temporada")
                elif parametro == "temperatura":
                    recomendaciones.append("Monitorear condiciones ambientales")

        # Si no hay recomendaciones específicas, agregar generales
        if not recomendaciones:
            recomendaciones.append("Mantener el programa de fertilización actual")

        historico = {
            "periodo": periodo,
            "periodo_texto": periodo_texto,
            "fechas": fechas,  # Array de fechas para el eje X
            "resumen": {
                "nitrogeno": {
                    "valor_actual": float(ultimo[1]),
                    "valor_anterior": float(anterior[1]),
                    "unidad": "ppm",
                    "icono": "🌱",
                    "descripcion": "El nitrógeno es esencial para el crecimiento vegetativo y el desarrollo de hojas.",
                    "tendencia": tendencias["nitrogeno"],
                    "datos_grafica": datos_nitrogeno,  # Array de valores para la gráfica
                    "color": "#4A6B2A",  # Verde para nitrógeno
                    "nombre": "Nitrógeno"
                },
                "fosforo": {
                    "valor_actual": float(ultimo[2]),
                    "valor_anterior": float(anterior[2]),
                    "unidad": "ppm",
                    "icono": "🧪",
                    "descripcion": "El fósforo favorece el desarrollo radicular y la formación de flores y frutos.",
                    "tendencia": tendencias["fosforo"],
                    "datos_grafica": datos_fosforo,
                    "color": "#6B9EBF",  # Azul para fósforo
                    "nombre": "Fósforo"
                },
                "potasio": {
                    "valor_actual": float(ultimo[3]),
                    "valor_anterior": float(anterior[3]),
                    "unidad": "ppm",
                    "icono": "🪴",
                    "descripcion": "El potasio mejora la resistencia a enfermedades y la calidad de los frutos.",
                    "tendencia": tendencias["potasio"],
                    "datos_grafica": datos_potasio,
                    "color": "#E8C662",  # Amarillo para potasio
                    "nombre": "Potasio"
                },
                "ph": {
                    "valor_actual": float(ultimo[4]),
                    "valor_anterior": float(anterior[4]),
                    "unidad": "",
                    "icono": "⚗️",
                    "descripcion": "El pH afecta la disponibilidad de nutrientes para las plantas.",
                    "tendencia": tendencias["ph"],
                    "datos_grafica": datos_ph,
                    "color": "#8B7BD8",  # Morado para pH
                    "nombre": "pH del suelo"
                },
                "humedad": {
                    "valor_actual": float(ultimo[5]),
                    "valor_anterior": float(anterior[5]),
                    "unidad": "%",
                    "icono": "💧",
                    "descripcion": "La humedad del suelo es crucial para la absorción de nutrientes.",
                    "tendencia": tendencias["humedad"],
                    "datos_grafica": datos_humedad,
                    "color": "#5DADE2",  # Azul claro para humedad
                    "nombre": "Humedad"
                },
                "temperatura": {
                    "valor_actual": float(ultimo[6]),
                    "valor_anterior": float(anterior[6]),
                    "unidad": "°C",
                    "icono": "🌡️",
                    "descripcion": "La temperatura afecta los procesos metabólicos de las plantas.",
                    "tendencia": tendencias["temperatura"],
                    "datos_grafica": datos_temperatura,
                    "color": "#F1948A",  # Rosa para temperatura
                    "nombre": "Temperatura"
                }
            },
            "analisis": {
                "tendencias_positivas": tendencias_positivas,
                "recomendaciones": recomendaciones
            },
            # Datos adicionales para gráficas combinadas si es necesario
            "datos_combinados": {
                "nutrientes": {
                    "fechas": fechas,
                    "series": [
                        {
                            "nombre": "Nitrógeno",
                            "datos": datos_nitrogeno,
                            "color": "#4A6B2A"
                        },
                        {
                            "nombre": "Fósforo", 
                            "datos": datos_fosforo,
                            "color": "#6B9EBF"
                        },
                        {
                            "nombre": "Potasio",
                            "datos": datos_potasio,
                            "color": "#E8C662"
                        }
                    ]
                },
                "condiciones": {
                    "fechas": fechas,
                    "series": [
                        {
                            "nombre": "pH",
                            "datos": datos_ph,
                            "color": "#8B7BD8"
                        },
                        {
                            "nombre": "Humedad (%)",
                            "datos": datos_humedad,
                            "color": "#5DADE2"
                        },
                        {
                            "nombre": "Temperatura (°C)",
                            "datos": datos_temperatura,
                            "color": "#F1948A"
                        }
                    ]
                }
            }
        }

        return historico

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- ENDPOINT ADICIONAL PARA GRÁFICA ESPECÍFICA -----------------
@router.get("/historico/{usuario_id}/{periodo}/{parametro}")
async def obtener_grafica_parametro(usuario_id: int, periodo: str, parametro: str):
    """
    Devuelve datos específicos para una gráfica individual de un parámetro.
    Parámetros válidos: nitrogeno, fosforo, potasio, ph, humedad, temperatura
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Validar parámetro
        parametros_validos = ["nitrogeno", "fosforo", "potasio", "ph", "humedad", "temperatura"]
        if parametro not in parametros_validos:
            raise HTTPException(status_code=400, detail="Parámetro inválido")

        # Definir fecha de consulta según período
        if periodo == "1mes":
            fecha_consulta = "DATEADD(MONTH, -1, GETDATE())"
        elif periodo == "3meses":
            fecha_consulta = "DATEADD(MONTH, -3, GETDATE())"
        else:
            fecha_consulta = "DATEADD(MONTH, -6, GETDATE())"

        # Query específica para el parámetro
        query = f"""
            SELECT 
                CAST(fecha_hora AS DATE) as fecha,
                AVG(CAST({parametro} AS FLOAT)) as valor
            FROM lecturas 
            WHERE usuario_id = ? AND fecha_hora >= {fecha_consulta}
            GROUP BY CAST(fecha_hora AS DATE)
            ORDER BY CAST(fecha_hora AS DATE)
        """
        
        cursor.execute(query, (usuario_id,))
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {"message": f"No hay datos históricos para {parametro}"}

        # Procesar datos
        fechas = [row[0].strftime("%Y-%m-%d") for row in results]
        valores = [float(row[1]) for row in results]

        # Información del parámetro
        info_parametros = {
            "nitrogeno": {"nombre": "Nitrógeno (N)", "unidad": "ppm", "color": "#4A6B2A", "icono": "🌱"},
            "fosforo": {"nombre": "Fósforo (P)", "unidad": "ppm", "color": "#6B9EBF", "icono": "🧪"},
            "potasio": {"nombre": "Potasio (K)", "unidad": "ppm", "color": "#E8C662", "icono": "🪴"},
            "ph": {"nombre": "pH del suelo", "unidad": "", "color": "#8B7BD8", "icono": "⚗️"},
            "humedad": {"nombre": "Humedad", "unidad": "%", "color": "#5DADE2", "icono": "💧"},
            "temperatura": {"nombre": "Temperatura", "unidad": "°C", "color": "#F1948A", "icono": "🌡️"}
        }

        return {
            "parametro": parametro,
            "info": info_parametros[parametro],
            "periodo": periodo,
            "fechas": fechas,
            "valores": valores,
            "valor_actual": valores[-1] if valores else 0,
            "valor_anterior": valores[-2] if len(valores) > 1 else valores[-1] if valores else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
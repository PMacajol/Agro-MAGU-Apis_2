from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, lecturas, actividades


app = FastAPI(
    title="AGROMAGU API",
    version="1.0.0",
    description="API para el sistema de monitoreo agrícola AGROMAGU"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas
app.include_router(auth.router)
app.include_router(lecturas.router)
app.include_router(actividades.router)

@app.get("/")
async def root():
    return {"message": "AGROMAGU API funcionando correctamente"}

@app.get("/api/health")
async def health_check():
    return {"status": "OK", "message": "API funcionando"}

#!/bin/bash
set -euo pipefail

log() { echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $*"; }

log "Inicio startup.sh"

# 1) Actualizar e instalar dependencias del sistema
apt-get update
apt-get install -y curl apt-transport-https gnupg ca-certificates build-essential unixodbc unixodbc-dev lsb-release

# 2) Añadir repositorio Microsoft y driver ODBC (intentamos ubuntu/debian)
log "Detectando distribución..."
CODENAME=$(lsb_release -cs 2>/dev/null || echo "bullseye")
log "Codename detectado: $CODENAME"

curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -  >/dev/null 2>&1 || true

if curl -fsSL "https://packages.microsoft.com/config/ubuntu/${CODENAME}/prod.list" -o /etc/apt/sources.list.d/mssql-release.list; then
  log "Usando repo para ubuntu/${CODENAME}"
else
  log "Falling back a debian 11 repo"
  curl -fsSL "https://packages.microsoft.com/config/debian/11/prod.list" -o /etc/apt/sources.list.d/mssql-release.list
fi

apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# limpiar cache apt
rm -rf /var/lib/apt/lists/*

# 3) Asegurar path a librerías
export LD_LIBRARY_PATH=/opt/microsoft/msodbcsql18/lib64:${LD_LIBRARY_PATH:-}

# 4) Instalar deps de python (porque desactivamos el build de Oryx)
log "Instalando dependencias Python desde requirements.txt"
python3 -m pip install --upgrade pip
python3 -m pip install -r /home/site/wwwroot/requirements.txt

# 5) Arrancar la app (reemplaza main:app si usas otro módulo)
log "Iniciando Gunicorn (UvicornWorker)"
exec /usr/local/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:${PORT} main:app

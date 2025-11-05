#!/bin/bash
echo "🚀 Iniciando Sistema JOSE018..."

# Instalar dependencias Node.js
echo "📦 Instalando dependencias Node.js..."
npm install

# Instalar dependencias Python
echo "🐍 Instalando dependencias Python..."
pip install -r requirements.txt

# Iniciar servicios en paralelo
echo "🔧 Iniciando servicios..."
node server.js &
python main.py &

# Mantener el script corriendo
wait

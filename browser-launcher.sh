#!/bin/bash
LAUNCHER_PY="$HOME/.local/share/browser-launcher/server.py"

# Matar cualquier proceso en el puerto 7700
fuser -k 7700/tcp 2>/dev/null
sleep 0.5

# Arrancar el servidor en segundo plano
python "$LAUNCHER_PY" &
SERVER_PID=$!

# Esperar a que esté listo
sleep 1

# Abrir la ventana como app
chromium --app=http://localhost:7700 --window-size=440,600 \
  --user-data-dir="$HOME/.local/share/browser-launcher/chromium-profile" \
  > /dev/null 2>&1 &

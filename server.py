#!/usr/bin/env python3
"""
Browser Launcher — servidor local para abrir navegadores reales
Uso: python server.py [puerto]
"""

import http.server
import json
import subprocess
import sys
import os
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs, unquote

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 7700

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Browser Launcher</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0f0f11;
    --surface: #1a1a1f;
    --border: #2a2a32;
    --accent: #e8ff47;
    --text: #e8e8ec;
    --muted: #5a5a6a;
    --radius: 8px;
  }

  body {
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg);
    color: var(--text);
    width: 420px;
    min-height: 100vh;
    padding: 20px;
    user-select: none;
  }

  header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }

  .logo {
    width: 28px; height: 28px;
    background: var(--accent);
    border-radius: 6px;
    display: grid;
    place-items: center;
    font-size: 14px;
  }

  h1 { font-size: 13px; font-weight: 700; color: var(--accent); letter-spacing: 0.15em; text-transform: uppercase; }
  .subtitle { font-size: 10px; color: var(--muted); letter-spacing: 0.1em; }

  .url-row { display: flex; gap: 8px; margin-bottom: 16px; }

  input[type="text"] {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    padding: 10px 12px;
    outline: none;
    transition: border-color 0.2s;
    user-select: text;
  }
  input[type="text"]:focus { border-color: var(--accent); }
  input[type="text"]::placeholder { color: var(--muted); }

  .btn-paste {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--muted);
    cursor: pointer;
    font-size: 14px;
    padding: 0 12px;
    transition: all 0.15s;
  }
  .btn-paste:hover { border-color: var(--accent); color: var(--accent); }

  .section-label { font-size: 9px; font-weight: 700; color: var(--muted); letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 10px; }

  .browsers-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }

  .browser-btn {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 600;
    padding: 11px 14px;
    transition: all 0.15s;
    position: relative;
    overflow: hidden;
  }
  .browser-btn.unavailable { opacity: 0.3; cursor: not-allowed; }
  .browser-btn::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--browser-color, var(--accent));
    opacity: 0;
    transition: opacity 0.15s;
  }
  .browser-btn:not(.unavailable):hover {
    border-color: var(--browser-color, var(--accent));
    background: color-mix(in srgb, var(--browser-color, var(--accent)) 8%, var(--surface));
    color: var(--browser-color, var(--accent));
    transform: translateY(-1px);
  }
  .browser-btn:not(.unavailable):hover::before { opacity: 1; }
  .browser-btn:active { transform: translateY(0); }
  .browser-icon { font-size: 18px; flex-shrink: 0; }

  .btn-all {
    width: 100%;
    background: color-mix(in srgb, var(--accent) 10%, var(--bg));
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    color: var(--accent);
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 11px;
    text-transform: uppercase;
    transition: all 0.15s;
    margin-bottom: 20px;
  }
  .btn-all:hover { background: var(--accent); color: var(--bg); }

  .divider { border: none; border-top: 1px solid var(--border); margin: 16px 0; }

  .quick-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
  .btn-add-quick {
    background: none;
    border: 1px dashed var(--border);
    border-radius: 5px;
    color: var(--muted);
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    padding: 3px 8px;
    transition: all 0.15s;
  }
  .btn-add-quick:hover { border-color: var(--accent); color: var(--accent); }

  .quick-list { display: flex; flex-direction: column; gap: 5px; }

  .quick-item {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 8px 10px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .quick-item:hover { border-color: var(--accent); }
  .quick-item:hover .quick-name { color: var(--accent); }
  .quick-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
  .quick-name { flex: 1; font-size: 11px; color: var(--text); transition: color 0.15s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .quick-url-text { font-size: 9px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 120px; }
  .quick-del { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 12px; padding: 0 2px; transition: color 0.15s; }
  .quick-del:hover { color: #ff6b6b; }

  .toast {
    position: fixed;
    bottom: 16px; left: 50%;
    transform: translateX(-50%) translateY(60px);
    background: var(--accent);
    color: var(--bg);
    font-size: 11px;
    font-weight: 700;
    padding: 8px 16px;
    border-radius: 20px;
    transition: transform 0.25s ease;
    pointer-events: none;
    white-space: nowrap;
    z-index: 999;
  }
  .toast.show { transform: translateX(-50%) translateY(0); }

  .modal-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.7);
    display: none;
    place-items: center;
    z-index: 100;
  }
  .modal-overlay.open { display: grid; }
  .modal { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; width: 300px; }
  .modal h2 { font-size: 13px; color: var(--accent); margin-bottom: 14px; }
  .modal label { font-size: 10px; color: var(--muted); display: block; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.15em; }
  .modal input {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    padding: 9px 10px;
    margin-bottom: 12px;
    outline: none;
    user-select: text;
  }
  .modal input:focus { border-color: var(--accent); }
  .modal-btns { display: flex; gap: 8px; }
  .modal-btns button { flex: 1; border: none; border-radius: 6px; cursor: pointer; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; padding: 10px; }
  #modal-cancel { background: var(--border); color: var(--muted); }
  #modal-save { background: var(--accent); color: var(--bg); }
</style>
</head>
<body>

<header>
  <div class="logo">🌐</div>
  <div>
    <h1>Browser Launcher</h1>
    <div class="subtitle">Cross-browser preview tool</div>
  </div>
</header>

<div class="url-row">
  <input type="text" id="url-input" placeholder="https://localhost:3000" />
  <button class="btn-paste" title="Pegar URL" onclick="pasteUrl()">📋</button>
</div>

<div class="section-label">Abrir en...</div>
<div class="browsers-grid" id="browsers-grid"></div>
<button class="btn-all" onclick="openAll()">⚡ Abrir en todos los navegadores</button>

<hr class="divider">

<div class="quick-urls">
  <div class="quick-title">
    <div class="section-label" style="margin:0">URLs rápidas</div>
    <button class="btn-add-quick" onclick="openModal()">+ Añadir</button>
  </div>
  <div class="quick-list" id="quick-list"></div>
</div>

<div class="toast" id="toast"></div>

<div class="modal-overlay" id="modal-overlay">
  <div class="modal">
    <h2>Nueva URL rápida</h2>
    <label>Nombre</label>
    <input type="text" id="modal-name" placeholder="Mi proyecto local" />
    <label>URL</label>
    <input type="text" id="modal-url" placeholder="http://localhost:8080" />
    <div class="modal-btns">
      <button id="modal-cancel" onclick="closeModal()">Cancelar</button>
      <button id="modal-save" onclick="saveQuick()">Guardar</button>
    </div>
  </div>
</div>

<script>
const BROWSERS = __BROWSERS_JSON__;
let quickUrls = JSON.parse(localStorage.getItem('bl-quick') || 'null') || [
  { name: 'Localhost 80',         url: 'http://localhost'              },
  { name: 'Localhost 3000',       url: 'http://localhost:3000'         },
  { name: 'Localhost 8080',       url: 'http://localhost:8080'         },
  { name: 'Staging Gaudirphotos', url: 'http://test.gaudirphotos.com'  },
];

function saveStorage() { localStorage.setItem('bl-quick', JSON.stringify(quickUrls)); }

// Render browser buttons
const grid = document.getElementById('browsers-grid');
BROWSERS.forEach(b => {
  const btn = document.createElement('button');
  btn.className = 'browser-btn' + (b.available ? '' : ' unavailable');
  btn.style.setProperty('--browser-color', b.color);
  btn.title = b.available ? '' : 'No encontrado en el sistema';
  btn.innerHTML = `<span class="browser-icon">${b.icon}</span>${b.name}`;
  if (b.available) btn.onclick = () => launch(b.cmd);
  grid.appendChild(btn);
});

function getUrl() {
  let u = document.getElementById('url-input').value.trim();
  if (!u) { showToast('Introduce una URL primero'); return null; }
  if (!u.match(/^https?:\/\//)) u = 'https://' + u;
  return u;
}

async function launch(cmd) {
  const url = getUrl();
  if (!url) return;
  try {
    const r = await fetch(`/launch?browser=${encodeURIComponent(cmd)}&url=${encodeURIComponent(url)}`);
    const d = await r.json();
    showToast(d.ok ? `Abriendo en ${cmd}…` : `Error: ${d.error}`);
  } catch(e) { showToast('Error al contactar con el servidor'); }
}

async function openAll() {
  const url = getUrl();
  if (!url) return;
  const available = BROWSERS.filter(b => b.available);
  for (const b of available) {
    await fetch(`/launch?browser=${encodeURIComponent(b.cmd)}&url=${encodeURIComponent(url)}`);
  }
  showToast(`Abriendo en ${available.length} navegadores…`);
}

async function pasteUrl() {
  try {
    const text = await navigator.clipboard.readText();
    document.getElementById('url-input').value = text;
  } catch { showToast('Permite el acceso al portapapeles'); }
}

// Quick URLs
function renderQuick() {
  const list = document.getElementById('quick-list');
  list.innerHTML = '';
  quickUrls.forEach((q, i) => {
    const item = document.createElement('div');
    item.className = 'quick-item';
    item.innerHTML = `
      <div class="quick-dot"></div>
      <div class="quick-name">${q.name}</div>
      <div class="quick-url-text">${q.url}</div>
      <button class="quick-del" title="Eliminar" onclick="event.stopPropagation();removeQuick(${i})">✕</button>
    `;
    item.onclick = () => { document.getElementById('url-input').value = q.url; };
    list.appendChild(item);
  });
}

function removeQuick(i) { quickUrls.splice(i, 1); saveStorage(); renderQuick(); }

function openModal() {
  document.getElementById('modal-name').value = '';
  document.getElementById('modal-url').value = '';
  document.getElementById('modal-overlay').classList.add('open');
  setTimeout(() => document.getElementById('modal-name').focus(), 50);
}
function closeModal() { document.getElementById('modal-overlay').classList.remove('open'); }
function saveQuick() {
  const name = document.getElementById('modal-name').value.trim();
  const url  = document.getElementById('modal-url').value.trim();
  if (!name || !url) { showToast('Rellena ambos campos'); return; }
  quickUrls.push({ name, url }); saveStorage(); renderQuick();
  closeModal(); showToast('URL añadida');
}
document.getElementById('modal-overlay').onclick = e => { if (e.target === e.currentTarget) closeModal(); };

let toastTimer;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
}

document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') { const av = BROWSERS.find(b => b.available); if (av) launch(av.cmd); }
});

renderQuick();
</script>
</body>
</html>
"""

# Lista de navegadores a detectar
BROWSERS = [
    {"name": "Firefox",   "icon": "🦊", "color": "#ff7139", "cmd": "firefox"},
    {"name": "Chromium",  "icon": "🔵", "color": "#4db6ff", "cmd": "chromium"},
    {"name": "Brave",     "icon": "🦁", "color": "#fb542b", "cmd": "brave"},
    {"name": "Chrome",    "icon": "🟡", "color": "#fbbc04", "cmd": "google-chrome-stable"},
    {"name": "Opera",     "icon": "🔴", "color": "#ff1b2d", "cmd": "opera"},
    {"name": "Vivaldi",   "icon": "🎭", "color": "#ef3939", "cmd": "vivaldi-stable"},
    {"name": "Librewolf", "icon": "🐺", "color": "#00b0ff", "cmd": "librewolf"},
    {"name": "Falkon",    "icon": "🌿", "color": "#4caf50", "cmd": "falkon"},
    {"name": "Konqueror", "icon": "🔷", "color": "#1e90ff", "cmd": "konqueror"},
    {"name": "Midori",    "icon": "🍃", "color": "#2ecc71", "cmd": "midori"},
]

def which(cmd):
    """Comprueba si el ejecutable está disponible."""
    try:
        result = subprocess.run(["which", cmd], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def detect_browsers():
    detected = []
    for b in BROWSERS:
        b_copy = dict(b)
        b_copy["available"] = which(b["cmd"])
        detected.append(b_copy)
    return detected

class Handler(http.server.BaseHTTPRequestHandler):
    browsers = []

    def log_message(self, format, *args):
        pass  # Silenciar logs por defecto

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            # Servir el HTML con la lista de navegadores inyectada
            browsers_json = json.dumps(self.browsers)
            page = HTML.replace("__BROWSERS_JSON__", browsers_json)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))

        elif parsed.path == "/launch":
            params = parse_qs(parsed.query)
            browser_cmd = unquote(params.get("browser", [""])[0])
            url = unquote(params.get("url", [""])[0])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            if not browser_cmd or not url:
                self.wfile.write(json.dumps({"ok": False, "error": "Faltan parámetros"}).encode())
                return

            try:
                subprocess.Popen(
                    [browser_cmd, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                self.wfile.write(json.dumps({"ok": True}).encode())
                print(f"  → {browser_cmd} {url}")
            except Exception as e:
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def main():
    browsers = detect_browsers()
    available = [b["name"] for b in browsers if b["available"]]

    print(f"\n🌐 Browser Launcher corriendo en http://localhost:{PORT}")
    print(f"   Navegadores detectados: {', '.join(available) if available else 'ninguno'}")
    print(f"   Ctrl+C para detener\n")

    Handler.browsers = browsers

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")

if __name__ == "__main__":
    main()

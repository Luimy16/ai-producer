#!/usr/bin/env python3
"""
Genera los notebooks de Colab (carpeta /notebooks) con tus tokens YA inyectados.

USO:
  1. Rellena antes  orquestador/.env  (WORKER_TOKEN y PUBLIC_API_URL)
  2. Ejecuta:       python3 generar_notebooks.py
  3. Sube la carpeta notebooks/ a tu repo de GitHub (¡MEJOR PRIVADO! llevan tu token)
  4. Configura launcher/index.html (bloque CFG) con tu repo

Después, al pulsar PLAY en la página Lanzador, las pestañas de Colab se abren
con el código ya cargado: solo hay que pulsar Ctrl+F9 en cada una.
"""
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "notebooks"
OUT.mkdir(exist_ok=True)

# ---- leer orquestador/.env ----
env = {}
env_path = BASE / "orquestador" / ".env"
if env_path.exists():
    for linea in env_path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            env[k.strip()] = v.strip()

WORKER_TOKEN = env.get("WORKER_TOKEN") or "PENDIENTE-RELLENAR-ENV"
API_URL = env.get("PUBLIC_API_URL") or "https://api.tudominio.com"
if "PENDIENTE" in WORKER_TOKEN or "tudominio" in API_URL:
    print("⚠️  AVISO: orquestador/.env no está rellenado; los notebooks saldrán con valores de ejemplo.")
    print("    Rellena .env y vuelve a ejecutar este script ANTES de subirlos a GitHub.\n")


def nb(cells):
    """Monta un .ipynb válido (nbformat 4)."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "colab": {"provenance": [], "gpuType": "T4"},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "accelerator": "GPU",
        },
        "cells": [
            {"cell_type": ("markdown" if md else "code"),
             "metadata": {},
             "source": src.splitlines(keepends=True),
             **({} if md else {"execution_count": None, "outputs": []})}
            for md, src in cells
        ],
    }


MD_COMUN = """# {emoji} Worker {rol} — VideoClip Creator

**ANTES DE EJECUTAR (solo la 1ª vez):** menú `Entorno de ejecución → Cambiar tipo de entorno de ejecución → GPU (T4)`.

**Después:** pulsa **`Ctrl+F9`** (o `Entorno de ejecución → Ejecutar todas`) y deja esta pestaña abierta.

Cuando veas `🟢 WORKER ACTIVO` al final, este worker ya se habrá **auto-registrado** en tu orquestador: vuelve a la página Lanzador y verás el ✅.

> ⏱ La primera ejecución tarda 5-10 min (descarga del modelo). Si Colab se desconecta, vuelve a pulsar `Ctrl+F9` (el worker se re-registrará solo con su nueva URL)."""

TUNEL = '''import subprocess, re, time, requests

proc = subprocess.Popen(['/content/cloudflared', 'tunnel', '--url', 'http://127.0.0.1:8080'],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
url = None
for _ in range(90):
    m = re.search(r'https://[a-z0-9-]+\\.trycloudflare\\.com', proc.stdout.readline())
    if m:
        url = m.group(0)
        break
assert url, 'No se pudo crear el túnel: reintenta esta celda'
print('🌐 URL pública del worker:', url)

API = '%%API_URL%%'
for intento in range(30):
    try:
        r = requests.post(API + '/api/workers/registrar',
                          json={'rol': '%%ROL%%', 'url': url},
                          headers={'X-Token': TOKEN}, timeout=20)
        print('✅ Auto-registrado en el orquestador:', r.json())
        break
    except Exception as e:
        print(f'  reintentando registro ({intento+1}/30)...', e)
        time.sleep(5)
else:
    print('❌ No se pudo registrar: revisa PUBLIC_API_URL y WORKER_TOKEN')

print()
print('🟢 WORKER ACTIVO. Vuelve al Lanzador: verás el check verde ✅')
print('   NO cierres esta pestaña mientras generas videoclips.')
while True:
    time.sleep(60)
'''

# ================= WORKER VIDEO (LTX-Video) =================
video_cells = [
    (True, MD_COMUN.format(emoji="🎬", rol="VIDEO")),
    (False, '''# CELDA 1 · Instalar dependencias (2-3 min)
!pip install -q --upgrade diffusers transformers accelerate sentencepiece \\
    imageio imageio-ffmpeg fastapi "uvicorn[standard]" nest-asyncio pillow
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \\
    -O /content/cloudflared && chmod +x /content/cloudflared
print('✅ instalación lista')'''),
    (False, '''# CELDA 2 · Cargar LTX-Video (modelo open source de Lightricks)
import torch
from diffusers import LTXImageToVideoPipeline

pipe = LTXImageToVideoPipeline.from_pretrained('Lightricks/LTX-Video', torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()   # necesario para caber en la T4 (15 GB)
print('✅ modelo cargado')'''),
    (False, '''# CELDA 3 · Servidor del worker (endpoint /video)
import base64, io, threading, time
import nest_asyncio, uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from PIL import Image
from diffusers.utils import export_to_video

TOKEN = '%%WORKER_TOKEN%%'   # inyectado por generar_notebooks.py
app = FastAPI()

@app.get('/ping')
def ping():
    return {'ok': True, 'rol': 'video'}

@app.post('/video')
def video(body: dict, x_token: str = Header(default='')):
    if x_token != TOKEN:
        raise HTTPException(401, 'token inválido')
    prompt   = body['prompt'] + ', cinematic, smooth motion, high quality'
    segundos = max(2.0, min(float(body.get('segundos', 5)), 8.0))
    fps      = 24
    frames   = int(segundos * fps) // 8 * 8 + 1   # LTXV exige frames ≡ 1 (mod 8)
    img = Image.open(io.BytesIO(base64.b64decode(body['imagen_b64']))).convert('RGB')
    img.thumbnail((768, 768))
    out = pipe(image=img, prompt=prompt, num_frames=frames, frame_rate=fps,
               num_inference_steps=25, guidance_scale=3.0).frames[0]
    path = f'/content/out_{int(time.time()*1000)}.mp4'
    export_to_video(out, path, fps=fps)
    return Response(content=open(path, 'rb').read(), media_type='video/mp4')

nest_asyncio.apply()
threading.Thread(target=lambda: uvicorn.run(app, host='127.0.0.1', port=8080), daemon=True).start()
time.sleep(5)
print('✅ servidor del worker corriendo')'''),
    (False, "# CELDA 4 · Túnel público + AUTO-REGISTRO en el orquestador\n" + TUNEL),
]

# ================= WORKER LIPSYNC (Wav2Lip) =================
lipsync_cells = [
    (True, MD_COMUN.format(emoji="💬", rol="LIPSYNC")),
    (False, '''# CELDA 1 · Instalar Wav2Lip (5-10 min la 1ª vez)
!git clone -q https://github.com/Rudrabha/Wav2Lip.git /content/Wav2Lip
!pip install -q gdown "librosa==0.8.1" "numba==0.56.4" "opencv-python-headless==4.8.1.78" \\
    fastapi "uvicorn[standard]" nest-asyncio
%cd /content/Wav2Lip
!gdown -q --fuzzy 'https://drive.google.com/file/d/15hwP0d7fyGkjb6IVmXqYPJB0TdkEecJ7/view' \\
    -O /content/wav2lip_gan.pth || echo '⚠️ si falla, descarga wav2lip_gan.pth a mano'
!wget -q https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth \\
    -O /content/Wav2Lip/face_detection/detection/sfd/s3fd.pth
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \\
    -O /content/cloudflared && chmod +x /content/cloudflared
import os
print('✅ instalación lista', '- checkpoint OK' if os.path.getsize('/content/wav2lip_gan.pth') > 1_000_000 else '- ⚠️ checkpoint pendiente')'''),
    (False, '''# CELDA 2 · Servidor del worker (endpoint /lipsync)
import base64, subprocess, threading, time, uuid
import nest_asyncio, uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response

TOKEN = '%%WORKER_TOKEN%%'   # inyectado por generar_notebooks.py
app = FastAPI()

@app.get('/ping')
def ping():
    return {'ok': True, 'rol': 'lipsync'}

@app.post('/lipsync')
def lipsync(body: dict, x_token: str = Header(default='')):
    if x_token != TOKEN:
        raise HTTPException(401, 'token inválido')
    uid = uuid.uuid4().hex[:8]
    v, a, o = f'/content/{uid}.mp4', f'/content/{uid}.wav', f'/content/{uid}_out.mp4'
    open(v, 'wb').write(base64.b64decode(body['video_b64']))
    open(a, 'wb').write(base64.b64decode(body['audio_b64']))
    subprocess.run(['python', '/content/Wav2Lip/inference.py',
                    '--checkpoint_path', '/content/wav2lip_gan.pth',
                    '--face', v, '--audio', a, '--outfile', o,
                    '--pads', '0', '15', '0', '0'],
                   check=True, capture_output=True)
    return Response(content=open(o, 'rb').read(), media_type='video/mp4')

nest_asyncio.apply()
threading.Thread(target=lambda: uvicorn.run(app, host='127.0.0.1', port=8080), daemon=True).start()
time.sleep(5)
print('✅ servidor lipsync corriendo')'''),
    (False, "# CELDA 3 · Túnel público + AUTO-REGISTRO en el orquestador\n" + TUNEL),
]

for nombre, rol, cells in [
    ("worker_video.ipynb", "video", video_cells),
    ("worker_lipsync.ipynb", "lipsync", lipsync_cells),
]:
    # inyectar secretos en las celdas de código
    for i, (md, src) in enumerate(cells):
        if not md:
            src = src.replace("%%WORKER_TOKEN%%", WORKER_TOKEN)
            src = src.replace("%%API_URL%%", API_URL)
            src = src.replace("%%ROL%%", rol)
            cells[i] = (md, src)
    ruta = OUT / nombre
    ruta.write_text(json.dumps(nb(cells), ensure_ascii=False, indent=1), encoding="utf-8")
    # validar que es JSON correcto
    json.loads(ruta.read_text(encoding="utf-8"))
    print(f"✅ generado notebooks/{nombre}")

print("\nSiguiente paso: sube la carpeta notebooks/ a tu repo de GitHub (recomendado: PRIVADO,")
print("porque los notebooks llevan tu WORKER_TOKEN) y configura CFG en launcher/index.html.")

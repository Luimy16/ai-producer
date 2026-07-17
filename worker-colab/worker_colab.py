# ============================================================================
# WORKER GPU GRATIS — Google Colab (VideoClip Creator)
# ----------------------------------------------------------------------------
# Este archivo se ejecuta en GOOGLE COLAB (GPU T4 gratis), NO en tu VPS.
# Pasos:
#   1. Abre https://colab.research.google.com → Nuevo notebook
#   2. Menú: Entorno de ejecución → Cambiar tipo de entorno → GPU (T4)
#   3. Copia CADA BLOQUE marcado como "CELDA n" en una celda nueva y ejecútalas en orden
#   4. Al final obtendrás una URL pública (trycloudflare.com): ponla como
#      WORKER_URL en el .env del orquestador y reinicia: docker compose restart orquestador
#
# OJO: Colab gratis desconecta la sesión tras unas horas o si está inactiva.
#      Si deja de responder, vuelve a ejecutar las celdas 3-5 y actualiza WORKER_URL.
# ============================================================================


# ============================ CELDA 1: instalar =============================
"""
!pip install -q --upgrade diffusers transformers accelerate sentencepiece \
    imageio imageio-ffmpeg fastapi "uvicorn[standard]" python-multipart nest-asyncio pillow
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /content/cloudflared
!chmod +x /content/cloudflared
print('✅ Instalación lista')
"""


# ====================== CELDA 2: cargar modelo de video =====================
# LTX-Video (Lightricks): open source, image-to-video, corre en la T4 gratis.
"""
import torch
from diffusers import LTXImageToVideoPipeline

pipe = LTXImageToVideoPipeline.from_pretrained(
    'Lightricks/LTX-Video', torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()   # imprescindible para caber en 15 GB de la T4
print('✅ Modelo LTX-Video cargado')
"""


# ====================== CELDA 3: servidor del worker ========================
"""
import base64, io, os, threading, time
import nest_asyncio, uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from PIL import Image
from diffusers.utils import export_to_video

WORKER_TOKEN = 'PON-AQUI-EL-MISMO-TOKEN-DEL-ENV'   # ← edítalo, igual que WORKER_TOKEN del .env

app = FastAPI()

def auth(t):
    if t != WORKER_TOKEN:
        raise HTTPException(401, 'token inválido')

@app.get('/ping')
def ping():
    return {'ok': True}

@app.post('/video')
def video(body: dict, x_token: str = Header(default='')):
    auth(x_token)
    prompt   = body['prompt'] + ', cinematic, smooth motion, high quality'
    segundos = max(2.0, min(float(body.get('segundos', 5)), 8.0))
    fps      = 24
    frames   = int(segundos * fps) // 8 * 8 + 1      # LTXV exige frames ≡ 1 (mod 8)
    img      = Image.open(io.BytesIO(base64.b64decode(body['imagen_b64']))).convert('RGB')
    img.thumbnail((768, 768))
    out = pipe(image=img, prompt=prompt, num_frames=frames, frame_rate=fps,
               num_inference_steps=25, guidance_scale=3.0).frames[0]
    path = f'/content/out_{int(time.time()*1000)}.mp4'
    export_to_video(out, path, fps=fps)
    return Response(content=open(path, 'rb').read(), media_type='video/mp4')

nest_asyncio.apply()
threading.Thread(target=lambda: uvicorn.run(app, host='127.0.0.1', port=8080),
                 daemon=True).start()
time.sleep(5)
print('✅ Servidor del worker corriendo en el puerto 8080')
"""


# ====================== CELDA 4: túnel público (gratis) =====================
"""
import subprocess, time, re
proc = subprocess.Popen(['/content/cloudflared', 'tunnel', '--url', 'http://127.0.0.1:8080'],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
url = None
for _ in range(60):
    linea = proc.stdout.readline()
    m = re.search(r'https://[a-z0-9-]+\\.trycloudflare\\.com', linea)
    if m:
        url = m.group(0); break
print()
print('=' * 70)
print('🌐 TU WORKER_URL ES:')
print(url)
print('=' * 70)
print('Cópiala en el .env del orquestador como WORKER_URL y reinicia el backend.')
import requests
print('Test /ping →', requests.get(url + '/ping', timeout=30).json())
"""


# ================= CELDA 5 (OPCIONAL): lipsync con Wav2Lip ==================
# Activa el endpoint /lipsync. Tarda ~10 min en prepararse la primera vez.
"""
!git clone -q https://github.com/Rudrabha/Wav2Lip.git /content/Wav2Lip
!pip install -q gdown librosa==0.8.1 numba==0.56.4 opencv-python-headless==4.8.1.78
!gdown -q 'https://drive.google.com/uc?id=15hwP0d7fyGkjb6IVmXqYPJB0TdkEecJ7' -O /content/wav2lip_gan.pth || \
!gdown -q '1dwFujX7I8OZPH1cHjVvPjNk0RHwI0iGDG' -O /content/wav2lip_gan.pth
!wget -q https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth -O /content/Wav2Lip/face_detection/detection/sfd/s3fd.pth
%cd /content/Wav2Lip

import base64, subprocess, uuid
from fastapi import Header, HTTPException
from fastapi.responses import Response

@app.post('/lipsync')
def lipsync(body: dict, x_token: str = Header(default='')):
    auth(x_token)
    uid = uuid.uuid4().hex[:8]
    v, a, o = f'/content/{uid}.mp4', f'/content/{uid}.wav', f'/content/{uid}_out.mp4'
    open(v, 'wb').write(base64.b64decode(body['video_b64']))
    open(a, 'wb').write(base64.b64decode(body['audio_b64']))
    subprocess.run(['python', 'inference.py', '--checkpoint_path', '/content/wav2lip_gan.pth',
                    '--face', v, '--audio', a, '--outfile', o,
                    '--pads', '0', '15', '0', '0'], check=True, capture_output=True)
    return Response(content=open(o, 'rb').read(), media_type='video/mp4')

print('✅ Endpoint /lipsync activo')
"""


# ==================== CELDA 6: mantener viva la sesión ======================
# Colab corta sesiones inactivas: deja esta celda corriendo mientras trabajas.
"""
import time
print('Manteniendo la sesión viva. NO cierres esta pestaña mientras generas videos.')
while True:
    time.sleep(60)
"""

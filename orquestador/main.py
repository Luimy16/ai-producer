"""
ORQUESTADOR — VideoClip Creator IA
==================================
Bot que hace TODO el pipeline:
  1. Analiza la canción (BPM, beats, duración)         → librosa (gratis, local)
  2. Escribe conceptos y storyboard                    → Gemini API (free tier)
  3. Genera personaje e imágenes de escena             → Pollinations/Flux (gratis)
  4. Anima cada escena (image-to-video)                → Workers GPU en Colab (gratis)
  5. Lipsync en escenas cantadas                       → Worker GPU (Wav2Lip)
  6. Ensambla el videoclip con el audio original       → FFmpeg (gratis, local)

Los workers de Colab se AUTO-REGISTRAN aquí (POST /api/workers/registrar),
así no hay que copiar URLs a mano: la página Lanzador los abre y ellos solos
notifican su URL pública.

Config por variables de entorno (ver .env.example).
"""
import base64
import json
import os
import subprocess
import time
import urllib.parse
import uuid
from pathlib import Path

import requests
from fastapi import FastAPI, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# librosa es opcional: si no instala, se usan escenas fijas de 5 s
try:
    import librosa
    TIENE_LIBROSA = True
except Exception:
    TIENE_LIBROSA = False

# ---------------- configuración ----------------
BASE = Path(__file__).resolve().parent
PROY = BASE / "proyectos"
PROY.mkdir(exist_ok=True)
WORKERS_FILE = BASE / "workers.json"

TOKEN        = os.getenv("VCC_TOKEN", "cambia-este-token")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
WORKER_URL   = os.getenv("WORKER_URL", "").rstrip("/")   # fallback manual (opcional)
WORKER_TOKEN = os.getenv("WORKER_TOKEN", "cambia-este-token")

app = FastAPI(title="Orquestador VideoClip Creator")

# CORS abierto: la página Lanzador (Cloudflare Pages/GitHub Pages) consulta /api/workers/estado.
# Las acciones sensibles siguen protegidas por tokens.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- utilidades ----------------
def auth(x_token: str = Header(default="")):
    if x_token != TOKEN:
        raise HTTPException(401, "Token inválido")


def ruta_proy(pid: str) -> Path:
    if not pid.replace("-", "").isalnum():
        raise HTTPException(400, "ID inválido")
    p = PROY / pid
    if not p.exists():
        raise HTTPException(404, "Proyecto no existe")
    return p


def cargar(pid: str) -> dict:
    return json.loads((ruta_proy(pid) / "estado.json").read_text(encoding="utf-8"))


def guardar(pid: str, estado: dict):
    (ruta_proy(pid) / "estado.json").write_text(
        json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")


def gemini(prompt: str):
    """Llama a Gemini (free tier) y devuelve JSON parseado."""
    if not GEMINI_KEY:
        raise HTTPException(500, "Falta GEMINI_API_KEY en el .env")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}")
    r = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }, timeout=180)
    r.raise_for_status()
    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(txt)


def imagen_gratis(prompt: str, destino: Path, w: int, h: int, seed: int = 42):
    """Genera imagen con Pollinations (Flux) — gratis, sin API key."""
    url = ("https://image.pollinations.ai/prompt/"
           + urllib.parse.quote(prompt[:1400])
           + f"?width={w}&height={h}&nologo=true&seed={seed}&model=flux")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    destino.write_bytes(r.content)


# ---------------- registro de workers (Colab) ----------------
def cargar_workers() -> dict:
    if WORKERS_FILE.exists():
        try:
            return json.loads(WORKERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def guardar_workers(w: dict):
    WORKERS_FILE.write_text(json.dumps(w, indent=2), encoding="utf-8")


def url_worker(rol: str) -> str:
    """URL del worker: primero el auto-registrado; si no, el fallback del .env."""
    w = cargar_workers()
    info = w.get(rol)
    if info and info.get("url"):
        return info["url"].rstrip("/")
    return WORKER_URL


def worker_post(endpoint: str, payload: dict, timeout: int = 900, rol: str = "") -> bytes:
    """Llama al worker GPU (Colab) y devuelve bytes (mp4)."""
    rol = rol or endpoint.strip("/").split("/")[0]
    base = url_worker(rol)
    if not base:
        raise HTTPException(
            500, f"No hay worker '{rol}' registrado: abre la página Lanzador, "
                 f"pulsa PLAY y ejecuta las celdas en Colab (Ctrl+F9).")
    r = requests.post(f"{base}{endpoint}", json=payload,
                      headers={"X-Token": WORKER_TOKEN}, timeout=timeout)
    r.raise_for_status()
    return r.content


def ffmpeg(*args: str):
    cmd = ["ffmpeg", "-y", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise HTTPException(500, "FFmpeg error: " + proc.stderr[-400:])


# ---------------- 1. crear proyecto + análisis ----------------
@app.post("/api/proyecto")
def nuevo_proyecto(audio: UploadFile, letra: str = Form(""),
                   formato: str = Form("16:9"), x_token: str = Header(default="")):
    auth(x_token)
    pid = uuid.uuid4().hex[:12]
    carpeta = PROY / pid
    carpeta.mkdir()
    audio_path = carpeta / "audio" + Path(audio.filename or ".mp3").suffix
    audio_path.write_bytes(audio.file.read())

    bpm, duracion, beats = 0, 0.0, []
    if TIENE_LIBROSA:
        try:
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
            duracion = float(librosa.get_duration(y=y, sr=sr))
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            bpm = round(float(tempo[0] if hasattr(tempo, "__len__") else tempo))
            beats = [round(float(t), 3) for t in librosa.frames_to_time(beat_frames, sr=sr)]
        except Exception:
            pass
    if duracion == 0:
        try:
            out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                                  "-of", "csv=p=0", str(audio_path)],
                                 capture_output=True, text=True).stdout.strip()
            duracion = float(out)
        except Exception:
            duracion = 180.0

    estado = {"id": pid, "letra": letra, "formato": formato, "bpm": bpm,
              "duracion": round(duracion, 1), "beats": beats[:600],
              "audio": audio_path.name, "conceptos": [], "concepto": None,
              "personaje": None, "escenas": [], "final": None}
    guardar(pid, estado)
    return {"id": pid, "bpm": bpm, "duracion": estado["duracion"], "formato": formato}


# ---------------- 2. conceptos ----------------
@app.post("/api/proyecto/{pid}/conceptos")
def conceptos(pid: str, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    data = gemini(f"""Eres un director de videoclips premiado. Letra de la canción:
\"\"\"{est['letra'][:3500]}\"\"\"
Propón 3 conceptos visuales MUY distintos (ej: fotorrealista, anime, cyberpunk, noir, onírico...).
Devuelve JSON: {{"conceptos":[{{"nombre":"...","descripcion":"2 frases de narrativa visual",
"paleta":"colores principales","personaje":"descripción física del protagonista para generar su imagen"}}]}}""")
    est["conceptos"] = data["conceptos"][:3]
    guardar(pid, est)
    return {"conceptos": est["conceptos"]}


# ---------------- 3. personaje ----------------
@app.post("/api/proyecto/{pid}/personaje")
def personaje(pid: str, body: dict, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    idx = body.get("concepto")
    estilo = est["conceptos"][idx]["nombre"] if isinstance(idx, int) and est["conceptos"] else "cinematográfico"
    desc = body.get("descripcion", "cantante protagonista")
    prompt = (f"character sheet, three views (front, profile, full body) of {desc}, "
              f"{estilo} style, consistent character, neutral background, detailed, high quality")
    w, h = (1216, 704) if est["formato"] == "16:9" else (704, 1216)
    destino = ruta_proy(pid) / "personaje.png"
    imagen_gratis(prompt, destino, w, h, seed=7)
    est["personaje"] = {"descripcion": desc, "archivo": "personaje.png"}
    guardar(pid, est)
    return {"url": f"/api/proyecto/{pid}/archivo/personaje.png"}


# ---------------- 4. storyboard ----------------
@app.post("/api/proyecto/{pid}/storyboard")
def storyboard(pid: str, body: dict, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    idx = body.get("concepto")
    if isinstance(idx, int):
        est["concepto"] = idx
    concepto = est["conceptos"][est["concepto"]] if est["conceptos"] and est["concepto"] is not None else {}
    n_escenas = max(4, round(est["duracion"] / 5))
    dur_escena = round(est["duracion"] / n_escenas, 1)

    data = gemini(f"""Eres director de videoclips. Canción de {est['duracion']}s, {est['bpm']} BPM.
Concepto visual elegido: {json.dumps(concepto, ensure_ascii=False)}
Personaje: {(est.get('personaje') or {}).get('descripcion', '')}
Letra: \"\"\"{est['letra'][:3500]}\"\"\"
Crea EXACTAMENTE {n_escenas} escenas de {dur_escena}s cada una, en orden, siguiendo la estructura
de la canción (intro, estrofa, coro...). Marca lipsync=true SOLO en escenas donde el personaje canta a cámara.
Cada prompt debe ser visual, detallado, en inglés, mencionando al personaje y el estilo "{concepto.get('nombre','')}".
Devuelve JSON: {{"escenas":[{{"seccion":"verso/chorus/...","prompt":"...","lipsync":false}}]}}""")

    escenas = []
    for i, e in enumerate(data["escenas"][:n_escenas]):
        escenas.append({"n": i, "seccion": e.get("seccion", ""), "prompt": e["prompt"],
                        "duracion": dur_escena, "lipsync": bool(e.get("lipsync")),
                        "imagen": None, "video": None})
    est["escenas"] = escenas
    guardar(pid, est)
    return {"escenas": escenas}


# ---------------- 5a. imagen de referencia por escena ----------------
@app.post("/api/proyecto/{pid}/escenas/{i}/imagen")
def escena_imagen(pid: str, i: int, body: dict, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    esc = est["escenas"][i]
    personaje_desc = (est.get("personaje") or {}).get("descripcion", "")
    prompt = body.get("prompt") or esc["prompt"]
    full = f"{prompt}. Main character: {personaje_desc}. Same character, cinematic still frame."
    w, h = (1216, 704) if est["formato"] == "16:9" else (704, 1216)
    destino = ruta_proy(pid) / f"escena_{i}.png"
    imagen_gratis(full, destino, w, h, seed=100 + i)
    esc["prompt"] = prompt
    esc["imagen"] = destino.name
    guardar(pid, est)
    return {"url": f"/api/proyecto/{pid}/archivo/{destino.name}"}


# ---------------- 5b. animar escena (worker GPU Colab) ----------------
@app.post("/api/proyecto/{pid}/escenas/{i}/video")
def escena_video(pid: str, i: int, body: dict, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    esc = est["escenas"][i]
    img_path = ruta_proy(pid) / (esc.get("imagen") or f"escena_{i}.png")
    if not img_path.exists():
        raise HTTPException(400, "Primero genera la imagen de la escena")
    payload = {
        "prompt": body.get("prompt") or esc["prompt"],
        "segundos": min(float(body.get("duracion") or esc["duracion"]), 8.0),
        "imagen_b64": base64.b64encode(img_path.read_bytes()).decode(),
    }
    mp4 = worker_post("/video", payload, rol="video")
    destino = ruta_proy(pid) / f"escena_{i}.mp4"
    destino.write_bytes(mp4)
    esc["video"] = destino.name
    guardar(pid, est)
    return {"url": f"/api/proyecto/{pid}/archivo/{destino.name}"}


# ---------------- 5c. lipsync (worker GPU Colab) ----------------
@app.post("/api/proyecto/{pid}/escenas/{i}/lipsync")
def escena_lipsync(pid: str, i: int, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    esc = est["escenas"][i]
    carpeta = ruta_proy(pid)
    video_path = carpeta / (esc.get("video") or f"escena_{i}.mp4")
    if not video_path.exists():
        raise HTTPException(400, "Primero genera el video de la escena")

    # extrae el fragmento exacto de la canción para esta escena
    inicio = round(sum(e["duracion"] for e in est["escenas"][:i]), 2)
    seg_path = carpeta / f"segmento_{i}.wav"
    ffmpeg("-ss", str(inicio), "-t", str(esc["duracion"]), "-i",
           str(carpeta / est["audio"]), "-ar", "16000", str(seg_path))

    payload = {
        "video_b64": base64.b64encode(video_path.read_bytes()).decode(),
        "audio_b64": base64.b64encode(seg_path.read_bytes()).decode(),
    }
    mp4 = worker_post("/lipsync", payload, rol="lipsync")
    destino = carpeta / f"escena_{i}_lip.mp4"
    destino.write_bytes(mp4)
    esc["video"] = destino.name
    guardar(pid, est)
    return {"url": f"/api/proyecto/{pid}/archivo/{destino.name}"}


# ---------------- 6. ensamblado final ----------------
@app.post("/api/proyecto/{pid}/ensamblar")
def ensamblar(pid: str, x_token: str = Header(default="")):
    auth(x_token)
    est = cargar(pid)
    carpeta = ruta_proy(pid)
    clips = [carpeta / e["video"] for e in est["escenas"] if e.get("video")]
    if not clips:
        raise HTTPException(400, "No hay escenas generadas")

    lista = carpeta / "lista.txt"
    lista.write_text("".join(f"file '{c.name}'\n" for c in clips))
    sin_audio = carpeta / "sin_audio.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", "lista.txt",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(sin_audio))

    final = carpeta / "videoclip_final.mp4"
    ffmpeg("-i", "sin_audio.mp4", "-i", est["audio"],
           "-c:v", "copy", "-c:a", "aac", "-shortest", str(final))

    est["final"] = final.name
    guardar(pid, est)
    return {"url": f"/api/proyecto/{pid}/archivo/{final.name}"}


# ---------------- workers: registro automático + estado ----------------
@app.post("/api/workers/registrar")
def registrar_worker(body: dict, x_token: str = Header(default="")):
    """Lo llama el notebook de Colab al arrancar: se autoregistra con su URL pública."""
    if x_token != WORKER_TOKEN:
        raise HTTPException(401, "Token de worker inválido")
    rol = str(body.get("rol", ""))
    url = str(body.get("url", "")).rstrip("/")
    if rol not in ("video", "lipsync") or not url.startswith("http"):
        raise HTTPException(400, "Datos inválidos")
    w = cargar_workers()
    w[rol] = {"url": url, "ts": time.time()}
    guardar_workers(w)
    return {"ok": True, "rol": rol, "url": url}


@app.get("/api/workers/estado")
def estado_workers():
    """Público (solo dice conectado sí/no): lo consulta la página Lanzador."""
    w = cargar_workers()
    ahora = time.time()
    return {
        rol: {
            "conectado": bool(w.get(rol, {}).get("url")),
            "hace_segundos": round(ahora - w[rol]["ts"]) if rol in w else None,
        }
        for rol in ("video", "lipsync")
    }


# ---------------- consultas ----------------
@app.get("/api/proyecto/{pid}")
def estado(pid: str, x_token: str = Header(default="")):
    auth(x_token)
    return cargar(pid)


@app.get("/api/proyecto/{pid}/archivo/{nombre}")
def archivo(pid: str, nombre: str, x_token: str = Header(default="")):
    auth(x_token)
    if "/" in nombre or ".." in nombre:
        raise HTTPException(400, "Nombre inválido")
    p = ruta_proy(pid) / nombre
    if not p.exists():
        raise HTTPException(404, "Archivo no existe")
    return FileResponse(str(p))

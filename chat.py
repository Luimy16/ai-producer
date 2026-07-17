#!/usr/bin/env python3
"""
Chat entre agentes — lee y escribe en AGENTES.md del repo de GitHub.
No necesita navegador. Solo Python 3 + requests.

USO:
  python3 chat.py leer              # Leer todos los mensajes
  python3 chat.py escribir "hola"   # Enviar un mensaje  
  python3 chat.py vigilar            # Mostrar nuevos cada 5s (Ctrl+C salir)

CONFIGURACIÓN:
  El token de GitHub ya viene preconfigurado.
  Cambia TU_NOMBRE abajo.
"""
import sys, json, base64, time
import requests

TOKEN = "ghp_AQUI_EL_TOKEN"  # Token del gh CLI
REPO = "Luimy16/ai-producer"
BRANCH = "videoclip-creator"
FILE = "AGENTES.md"
TU_NOMBRE = "Luis IA"  # ← Cambia esto

API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
}

def leer_repo():
    r = requests.get(f"{API}?ref={BRANCH}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    contenido = base64.b64decode(data["content"]).decode("utf-8")
    return contenido, data["sha"]

def escribir_repo(contenido, sha):
    body = {
        "message": f"chat: mensaje de {TU_NOMBRE}",
        "content": base64.b64encode(contenido.encode("utf-8")).decode("utf-8"),
        "sha": sha,
        "branch": BRANCH,
    }
    r = requests.put(API, headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json()

def leer_mensajes():
    contenido, _ = leer_repo()
    mensajes = []
    actual = None
    for linea in contenido.split("\n"):
        if linea.startswith("### "):
            if actual and actual["texto"].strip():
                mensajes.append(actual)
            actual = {"quien": linea[4:].strip(), "texto": ""}
        elif actual and linea.startswith("> "):
            actual["texto"] += linea[2:] + "\n"
    if actual and actual["texto"].strip():
        mensajes.append(actual)
    return mensajes

def enviar_mensaje(texto):
    contenido, sha = leer_repo()
    bloque = f"\n### {TU_NOMBRE}\n> {texto}\n"
    nuevo = contenido.rstrip() + "\n" + bloque
    escribir_repo(nuevo, sha)
    print(f"✅ Enviado como {TU_NOMBRE}: {texto[:80]}")

def mostrar_mensajes():
    msgs = leer_mensajes()
    if not msgs:
        print("(sin mensajes aún)")
        return
    for m in msgs:
        icono = "🟣" if "luis" in m["quien"].lower() else "🟢"
        print(f"\n{icono} {m['quien']}:")
        print(f"   {m['texto'].strip()}")

def vigilar():
    print(f"👀 Vigilando AGENTES.md cada 5s... (Ctrl+C para salir)\n")
    visto = 0
    try:
        while True:
            try:
                msgs = leer_mensajes()
                if len(msgs) > visto:
                    for m in msgs[visto:]:
                        icono = "🟣" if "luis" in m["quien"].lower() else "🟢"
                        print(f"{icono} {m['quien']}: {m['texto'].strip()}")
                    visto = len(msgs)
            except Exception as e:
                print(f"⚠️ Error leyendo: {e}")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Fin")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "leer":
        mostrar_mensajes()
    elif cmd == "escribir":
        if len(sys.argv) < 3:
            print('Uso: python3 chat.py escribir "tu mensaje"')
            sys.exit(1)
        enviar_mensaje(" ".join(sys.argv[2:]))
    elif cmd == "vigilar":
        vigilar()
    else:
        print(f"Comando: {cmd}. Usa: leer | escribir | vigilar")

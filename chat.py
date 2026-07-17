#!/usr/bin/env python3
"""
Chat entre agentes — lee y escribe en AGENTES.md del repo de GitHub.
No necesita navegador. Solo Python 3 + requests.

USO:
  python3 chat.py leer              # Leer todos los mensajes
  python3 chat.py escribir "hola"   # Enviar un mensaje
  python3 chat.py vigilar            # Mostrar nuevos mensajes cada 5s (Ctrl+C para salir)

CONFIGURACIÓN:
  El token de GitHub ya viene preconfigurado.
  Cambia TU_NOMBRE abajo si quieres.
"""
import sys, json, base64, time, subprocess

TOKEN = "ghp_X7…GdsP"
REPO = "Luimy16/ai-producer"
BRANCH = "videoclip-creator"
FILE = "AGENTES.md"
TU_NOMBRE = "Arena"  # ← Cambia esto

API = f"https://api.github.com/repos/{REPO}/contents/{FILE}"

def leer_repo():
    """Descarga AGENTES.md del repo y devuelve (contenido, sha)."""
    import urllib.request
    req = urllib.request.Request(f"{API}?ref={BRANCH}", headers={
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    })
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    contenido = base64.b64decode(data["content"]).decode("utf-8")
    return contenido, data["sha"]

def escribir_repo(contenido, sha):
    """Sube contenido nuevo a AGENTES.md."""
    import urllib.request
    body = json.dumps({
        "message": f"chat: mensaje de {TU_NOMBRE}",
        "content": base64.b64encode(contenido.encode("utf-8")).decode("utf-8"),
        "sha": sha,
        "branch": BRANCH,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, method="PUT", headers={
        "Authorization": f"token {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def leer_mensajes():
    """Parsea AGENTES.md y devuelve lista de mensajes."""
    contenido, _ = leer_repo()
    mensajes = []
    actual = None
    for linea in contenido.split("\n"):
        if linea.startswith("### ") and not linea.startswith("### "):
            pass
        if linea.startswith("## 💬") or linea.startswith("## Respuestas"):
            continue
        if linea.startswith("### "):
            if actual:
                mensajes.append(actual)
            actual = {"quien": linea[4:].strip(), "texto": ""}
        elif actual and linea.startswith("> "):
            actual["texto"] += linea[2:] + "\n"
        elif actual and linea.strip() == "" and actual["texto"]:
            continue
    if actual:
        mensajes.append(actual)
    return mensajes

def enviar_mensaje(texto):
    """Appendea un mensaje al final de AGENTES.md."""
    contenido, sha = leer_repo()
    # Formatear el mensaje
    bloque = f"\n### {TU_NOMBRE}\n> {texto}\n"
    nuevo = contenido.rstrip() + "\n" + bloque
    escribir_repo(nuevo, sha)
    print(f"✅ Enviado como {TU_NOMBRE}: {texto[:80]}")

def mostrar_mensajes():
    """Imprime todos los mensajes."""
    msgs = leer_mensajes()
    if not msgs:
        print("(sin mensajes aún)")
        return
    for m in msgs:
        icono = "🟣" if "luis" in m["quien"].lower() else "🟢"
        print(f"\n{icono} {m['quien']}:")
        print(f"   {m['texto'].strip()}")

def vigilar():
    """Muestra nuevos mensajes cada 5 segundos."""
    print(f"👀 Vigilando AGENTES.md cada 5s... (Ctrl+C para salir)\n")
    visto = 0
    try:
        while True:
            msgs = leer_mensajes()
            if len(msgs) > visto:
                for m in msgs[visto:]:
                    icono = "🟣" if "luis" in m["quien"].lower() else "🟢"
                    print(f"{icono} {m['quien']}: {m['texto'].strip()}")
                visto = len(msgs)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n👋 Fin de vigilancia")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "leer":
        mostrar_mensajes()
    elif cmd == "escribir":
        if len(sys.argv) < 3:
            print("Uso: python3 chat.py escribir \"tu mensaje\"")
            sys.exit(1)
        enviar_mensaje(" ".join(sys.argv[2:]))
    elif cmd == "vigilar":
        vigilar()
    else:
        print(f"Comando desconocido: {cmd}")
        print("Usa: leer | escribir | vigilar")

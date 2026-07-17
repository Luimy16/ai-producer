# 🎬 VideoClip Creator IA — Versión 100% GRATIS (con Lanzador automático)

> Réplica del sistema de Limbus Videoclip Creator con coste **0 €/mes**.
> El bot hace todo: **guion → personajes → fotos → animación → lipsync → edición final**.
> Y con la página **Lanzador**: pulsas PLAY → se abren las pestañas de Colab con el código ya cargado → solo hace falta `Ctrl+F9` en cada una → los workers se conectan solos.

---

## ⭐ Cómo se usa cada día (una vez instalado)

```
1. Abres tu página Lanzador  →  https://TU-LAUNCHER.pages.dev
2. Pulsas  ▶ PLAY
3. Se abren 2 pestañas de Google Colab CON EL CÓDIGO YA PUESTO (no pegas nada)
4. En cada pestaña: Ctrl+F9   ← lo único manual, Google obliga a este clic
5. Los workers se AUTO-REGISTRAN en tu servidor → ves ✅ en el Lanzador
6. Entras al creador y haces tu videoclip
```

**¿Por qué no puede ser 100% automático?** Ninguna página web puede ejecutar código dentro de Colab por ti: Google lo bloquea por seguridad (igual que ninguna web puede escribir dentro de tu Gmail). El sistema deja todo listo para que el único gesto sea `Ctrl+F9` por pestaña. Es el máximo de automatización posible sin pagar GPU.

---

## 1. Arquitectura completa

```
LANZADOR (Cloudflare Pages)          VPS GRATIS (Oracle)                 COLAB (GPU gratis)
┌────────────────────┐   estado ✅   ┌──────────────────────────────┐    ┌────────────────────────┐
│ index.html         │──────────────▶│ ORQUESTADOR (FastAPI)        │    │ worker_video.ipynb     │
│  · botón PLAY      │               │ 1. librosa → BPM     GRATIS  │    │  LTX-Video (animar)    │
│  · abre pestañas ──┼───────────────┼─▶ notebooks desde GitHub     │    └──────────┬─────────────┘
│  · panel de estado │◀──────────────│ 2. Gemini → guion    GRATIS  │◀─── auto-registro URL      │
└────────────────────┘               │ 3. Pollinations → fotos      │    ┌────────────────────────┐
                                     │ 6. FFmpeg → montaje  GRATIS  │◀───│ worker_lipsync.ipynb   │
WORDPRESS (mismo VPS)                │ 5. workers.json (registro)   │    │  Wav2Lip (cantar)      │
└ plugin [videoclip_creator] ───────▶│ 4. reparte trabajos a Colab  │    └────────────────────────┘
                                     └──────────────────────────────┘
```

| Pieza | Tecnología gratis | Límite |
|---|---|---|
| Dominio + DNS + CDN + SSL | Cloudflare | ilimitado |
| Lanzador (página estática) | Cloudflare Pages o GitHub Pages | ilimitado |
| WordPress + bot + BD | **Oracle Cloud Always Free** (ARM, 24 GB RAM) | gratis para siempre |
| Guion/storyboard | **Gemini API free tier** | ~1.500 peticiones/día |
| Fotos (personaje/escenas) | **Pollinations.ai** (Flux) | gratis, con cola si hay carga |
| Animación (video) | **LTX-Video** en **Google Colab** (T4) | sesiones de horas; si se corta, PLAY otra vez |
| Lipsync | **Wav2Lip** (segundo Colab) | igual |
| Ensamblaje | **FFmpeg** en el VPS | ilimitado |

---

## 2. Cuentas gratis (10 min)

1. **Google AI Studio** → [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → *Create API key* (será `GEMINI_API_KEY`). Sin tarjeta.
2. **Oracle Cloud** → [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) (pide tarjeta solo para verificar; el tier Always Free no cobra).
3. **Cloudflare** → añade tu dominio (plan Free) y apunta los nameservers en tu registrador.
4. **GitHub** → crea un repo para este proyecto (mejor **PRIVADO**: los notebooks llevarán tu token).

---

## 3. VPS gratis: Oracle Cloud (15 min)

1. **Compute → Instances → Create instance**: imagen **Ubuntu 22.04 (aarch64)**, shape **VM.Standard.A1.Flex** (2 OCPU / 12 GB, "Always Free-eligible"), descarga la clave SSH.
2. Abre puertos en Oracle: VCN → Security Lists → Ingress Rules → TCP **80**, **443** y **8000** desde `0.0.0.0/0`.
3. Por SSH:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
```

4. En **Cloudflare → DNS** (proxy naranja ON):
   - `A` → `tudominio.com` → IP del VPS (WordPress)
   - `A` → `api.tudominio.com` → IP del VPS (orquestador, puerto 8000)

---

## 4. Configura y despliega (10 min)

En tu PC, dentro de la carpeta del proyecto:

```bash
# 1. Secretos
cp orquestador/.env.example orquestador/.env
nano orquestador/.env
#   VCC_TOKEN       → invéntalo (largo)
#   GEMINI_API_KEY  → la de AI Studio
#   WORKER_TOKEN    → otro distinto (largo)
#   PUBLIC_API_URL  → https://api.tudominio.com
#   DB_PASSWORD     → contraseña de la base de datos

# 2. Genera los notebooks de Colab CON tus tokens inyectados
python3 generar_notebooks.py        # crea /notebooks/worker_video.ipynb y worker_lipsync.ipynb

# 3. Edita la página Lanzador: launcher/index.html → bloque CFG (arriba del script):
#      repo: "tu-usuario/tu-repo", api: "https://api.tudominio.com",
#      creador: "https://tudominio.com/crear-videoclip"

# 4. Sube TODO a tu repo de GitHub (PRIVADO recomendado)
git init && git add -A && git commit -m "videoclip creator"
git remote add origin https://github.com/tu-usuario/tu-repo.git
git push -u origin main

# 5. Despliega web + bot en el VPS
scp -r ../mi-videoclip-creator ubuntu@IP-DEL-VPS:~/
ssh ubuntu@IP-DEL-VPS
cd ~/mi-videoclip-creator && docker compose up -d --build
```

> 📌 GitHub Pages **no ejecuta PHP**: GitHub guarda el código y sirve los notebooks a Colab; la web vive en el VPS.

---

## 5. Publica el Lanzador (5 min)

**Opción A — Cloudflare Pages (recomendada):**
1. Cloudflare → **Workers & Pages → Create → Pages → Connect to Git** → tu repo.
2. Framework: *None* · Build command: *(vacío)* · Output dir: `/`
3. Tu Lanzador queda en `https://tu-proyecto.pages.dev/launcher/`

**Opción B — GitHub Pages:** Settings → Pages → rama `main` → queda en `https://tu-usuario.github.io/tu-repo/launcher/`

---

## 6. WordPress (5 min)

1. `http://tudominio.com` → asistente → crea el admin.
2. **Plugins** → activa **VideoClip Creator IA**.
3. **Ajustes → VideoClip Creator** → URL `http://127.0.0.1:8000` + el `VCC_TOKEN`.
4. **Páginas → Añadir** → pega `[videoclip_creator]` → publica con slug `crear-videoclip`.

---

## 7. Primer encendido con el Lanzador 🚀

1. Abre tu Lanzador → **PLAY** (permite ventanas emergentes si el navegador lo pide).
2. Se abren 2 pestañas de Colab **con el código ya cargado desde tu GitHub**.
   - Primera vez en Colab: inicia sesión con Google y, si el repo es privado, marca *"include private repos"* al autorizar GitHub.
3. En cada pestaña: comprueba GPU (**Entorno de ejecución → Cambiar tipo → T4**) y pulsa **Ctrl+F9**.
4. Espera (5-10 min la 1ª vez): al final de cada notebook verás `🟢 WORKER ACTIVO` → en el Lanzador aparecerá el ✅ (se auto-registraron solos).
5. Botón **"Ir al creador de videoclips"** → flujo de 5 pasos: canción → concepto → personaje → storyboard → generar → descargar MP4.

> 🔁 Colab gratis se corta tras horas: si un worker deja de responder → PLAY otra vez + Ctrl+F9. Como el registro es automático, no hay que copiar ninguna URL nunca.

---

## 8. Upgrade a pago (opcional, cuando valides)

Cambia solo el "proveedor de video" en `orquestador/main.py` (función `escena_video`): llama a **fal.ai** (Kling 3.0, ~0,07 $/s) en vez del worker de Colab. Unas 10 líneas; todo lo demás queda igual.

## 9. Archivos

```
mi-videoclip-creator/
├── GUIA-GRATIS.md
├── docker-compose.yml
├── generar_notebooks.py           ← inyecta tokens y crea los .ipynb
├── notebooks/                     ← se generan y suben a tu GitHub
│   ├── worker_video.ipynb         (LTX-Video: anima las fotos)
│   └── worker_lipsync.ipynb       (Wav2Lip: personajes que cantan)
├── launcher/index.html            ← LA PÁGINA DEL BOTÓN PLAY
├── plugin/videoclip-creator/      ← plugin WP (shortcode + proxy seguro)
└── orquestador/                   ← EL BOT (FastAPI) + Dockerfile + .env.example
```

## 10. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Las pestañas no se abren | Permite popups en el Lanzador o usa los botones manuales que aparecen |
| Colab dice "notebook no encontrado" | Repo privado sin autorizar: en Colab, File → Open → GitHub → marca *include private repos* |
| "No hay worker registrado" al generar | Aún no terminó Ctrl+F9 en Colab, o el registro falló: revisa `PUBLIC_API_URL` y puerto 8000 abierto |
| Error 401 en registro | `WORKER_TOKEN` del .env ≠ del notebook → re-ejecuta `generar_notebooks.py` y sube otra vez |
| Lanzador dice "API sin responder" | DNS `api.tudominio.com` no apunta al VPS, o `docker compose up -d` no está corriendo |
| Colab se desconectó | PLAY otra vez → Ctrl+F9 → se re-registra solo |

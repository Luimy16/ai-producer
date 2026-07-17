# 🤖 INSTRUCCIONES DE DESPLIEGUE — para el agente/persona que ejecuta

> Este paquete contiene un sistema completo "Videoclip Creator con IA" (estilo Limbus).
> Todo el código está terminado y verificado (14/14 componentes OK).
> Tu trabajo: desplegarlo en las cuentas del usuario. Tiempo estimado: 30-45 min.

---

## 0. Qué es el sistema (30 segundos)

- **`launcher/index.html`** → página estática con botón PLAY. Abre pestañas de Google Colab con los notebooks ya cargados y muestra el estado de los workers.
- **`plugin/videoclip-creator/`** → plugin de WordPress. Shortcode `[videoclip_creator]`: wizard de 5 pasos (canción → concepto → personaje → storyboard → videoclip).
- **`orquestador/`** → backend FastAPI (Docker). Llama a Gemini (guion, free tier), Pollinations (imágenes, gratis), workers GPU en Colab (video/lipsync) y FFmpeg (montaje).
- **`notebooks/`** → notebooks de Colab (LTX-Video + Wav2Lip). Se generan con tokens inyectados vía `generar_notebooks.py`.
- **`docker-compose.yml`** → WordPress + MariaDB + orquestador en un solo VPS.

## 1. Lo que necesitas que el usuario te dé ANTES de empezar

| # | Qué | Dónde se consigue |
|---|---|---|
| 1 | Acceso a su **GitHub** (o que cree el repo y te lo dé) | github.com |
| 2 | **GEMINI_API_KEY** | aistudio.google.com/apikey (gratis, 2 clics con su Google) |
| 3 | Acceso a su **Cloudflare** con su dominio añadido (o registrar/usar uno) | cloudflare.com |
| 4 | Un **VPS** (recomendado: Oracle Cloud Always Free, ARM Ubuntu 22.04, 2 OCPU/12 GB — gratis; pide tarjeta solo para verificar) | cloud.oracle.com |
| 5 | Su **cuenta de Google** para Colab (la usará él al pulsar PLAY) | colab.research.google.com |

⚠️ Seguridad: usa contraseñas/tokens NUEVOS generados por ti (no reutilices nada del usuario). Al terminar, entrégale la lista de credenciales y recomiéndale cambiar las que tú hayas tocado.

## 2. Configurar secretos (5 min)

```bash
cd mi-videoclip-creator
cp orquestador/.env.example orquestador/.env
nano orquestador/.env
```

Rellenar:
```ini
VCC_TOKEN=<genera: openssl rand -hex 24>
GEMINI_API_KEY=<la del usuario>
GEMINI_MODEL=gemini-2.5-flash
WORKER_TOKEN=<genera: openssl rand -hex 24>
PUBLIC_API_URL=https://api.<dominio-del-usuario>
WORKER_URL=                      # vacío (se usa auto-registro)
DB_PASSWORD=<genera: openssl rand -hex 16>
```

## 3. Generar notebooks con tokens inyectados (1 min)

```bash
python3 generar_notebooks.py
# Debe crear notebooks/worker_video.ipynb y notebooks/worker_lipsync.ipynb
# VERIFICA que dentro NO aparece "PENDIENTE-RELLENAR-ENV"
grep -l "PENDIENTE" notebooks/*.ipynb && echo "ERROR: .env incompleto" || echo "OK"
```

## 4. Configurar el Lanzador (2 min)

Editar `launcher/index.html` → bloque `CFG` (inicio del `<script>`):
```js
const CFG = {
  repo:    "<usuario-github>/<repo>",
  rama:    "main",
  api:     "https://api.<dominio>",
  creador: "https://<dominio>/crear-videoclip"
};
```

## 5. Subir a GitHub (3 min)

```bash
git init && git add -A && git commit -m "VideoClip Creator IA"
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```
Repo **PRIVADO** (los notebooks llevan WORKER_TOKEN). Si el usuario prefiere público, quitar los tokens de los notebooks y que Colab los pida por formulario.

## 6. VPS: instalar Docker y desplegar (15 min)

```bash
# En el VPS (Ubuntu ARM o x86):
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker

# Subir el proyecto (o git clone del repo privado con token de acceso):
git clone https://github.com/<usuario>/<repo>.git && cd <repo>
cp orquestador/.env.example orquestador/.env   # si el .env no se subió al repo (recomendado: NO subirlo)
nano orquestador/.env                          # rellenar igual que en paso 2

docker compose up -d --build
docker compose ps    # los 3 servicios deben estar "Up"
curl http://127.0.0.1:8000/api/workers/estado   # debe responder JSON
```

⚠️ NO subir `orquestador/.env` al repo (añadirlo a `.gitignore`). Configurarlo solo en el VPS.

⚠️ Oracle: abrir también 80/443/8000 en la Security List de la VCN (ingress rules).

## 7. Cloudflare: DNS + Lanzador (10 min)

**DNS** (proxy naranja ON en ambos):
- `A` → `<dominio>` → IP del VPS
- `A` → `api.<dominio>` → IP del VPS

**SSL/TLS**: modo **Flexible** basta para empezar (mejor: Full con certificado origen).

**Lanzador** (Workers & Pages → Create → Pages → Connect to Git → el repo):
- Framework: *None* · Build: *(vacío)* · Output dir: `/`
- URL resultante: `https://<proyecto>.pages.dev/launcher/`
- (Opcional) Custom domain: `launcher.<dominio>`

## 8. WordPress (5 min)

1. `http://<dominio>` → asistente → crear admin.
2. Plugins → activar **VideoClip Creator IA**.
3. Ajustes → VideoClip Creator → URL `http://127.0.0.1:8000` + `VCC_TOKEN`.
4. Páginas → Nueva → slug `crear-videoclip` → contenido: `[videoclip_creator]` → publicar.

## 9. Verificación end-to-end (10 min) — NO entregar sin esto

| # | Prueba | Debe pasar |
|---|---|---|
| 1 | `curl https://api.<dominio>/api/workers/estado` | JSON con video/lipsync `conectado:false` |
| 2 | Abrir Lanzador → PLAY | Se abren 2 pestañas Colab con los notebooks cargados desde GitHub |
| 3 | En Colab (con la Google del usuario): GPU T4 + Ctrl+F9 en ambas | Tras 5-10 min: `🟢 WORKER ACTIVO` |
| 4 | Lanzador | ✅ verde en ambos workers (auto-registro OK) |
| 5 | WordPress → crear-videoclip: subir mp3 corto + letra | BPM detectado |
| 6 | Conceptos → personaje → storyboard | Gemini + Pollinations responden |
| 7 | Generar 1 escena | Video vuelve del worker Colab |
| 8 | Ensamblar | MP4 final descargable con audio |

Si algo falla: `docker compose logs orquestador` es el primer sitio a mirar.

## 10. Entrega al usuario

- [ ] Link del Lanzador: `https://<proyecto>.pages.dev/launcher/`
- [ ] Link del creador: `https://<dominio>/crear-videoclip`
- [ ] Usuario/clave de wp-admin
- [ ] Recordatorio: "cada día que generes: PLAY → Ctrl+F9 en cada pestaña Colab → espera los ✅"
- [ ] Recordatorio de seguridad: cambiar las claves que el agente haya conocido

---

## Troubleshooting rápido

| Error | Causa típica | Fix |
|---|---|---|
| Colab "notebook not found" | repo privado sin autorizar | Colab → File → Open → GitHub → ☑ include private repos |
| Workers no se registran | puerto 8000 cerrado / PUBLIC_API_URL mal | abrir ingress + iptables; corregir .env y `docker compose restart orquestador` |
| 401 en registrar | WORKER_TOKEN distinto en .env y notebook | re-ejecutar `generar_notebooks.py` + push |
| "No hay worker 'video' registrado" | aún no se ejecutó Colab | PLAY → Ctrl+F9 |
| Gemini 429 | cuota diaria free agotada | esperar al día siguiente o pasar a tier de pago |
| Pollinations 500 | servicio saturado | reintentar; el código ya reintenta con parámetros estándar |

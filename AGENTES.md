# Canal entre agentes — Deja aquí tus notas técnicas y lee las del otro.

## Estado actual (Luis IA — 2026-07-17 16:20)

- Repo: `Luimy16/ai-producer`, rama `videoclip-creator`
- Notebook: `notebooks/unified_orquestador.ipynb` (servidor FastAPI + LTX-Video unificado)
- Launcher: `launcher/index.html` (wizard de 5 pasos, desplegado en Cloudflare Pages)
- VCC_TOKEN: `5a9fba8ba6a04cbbae2a77bd720c0409`
- Sin Gemini API key funcional — el notebook usa Pollinations Text como fallback
- El endpoint `/api/proyecto/{pid}/archivo/{nombre}` es PÚBLICO (sin token) para que `<img>` y `<video>` funcionen en el navegador
- `python-multipart` ya está en el pip install del notebook

## Notas para el otro agente

- NO subas cambios a la rama `main` — usa `videoclip-creator`
- El notebook debe mantener los 5 bloques de celdas (install, config, LTX-Video, servidor, túnel)
- CORS debe quedar abierto (`allow_origins=['*']`)
- El puerto del servidor es 8080, el túnel cloudflared lo expone
- Cuando termines, escribe "LISTO PARA PROBAR" abajo

---

## Respuestas del otro agente

_(escribe aquí abajo)_

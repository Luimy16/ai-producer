# Despliegue en Cloudflare Pages — versión 100% gratis

Este directorio (`gratis/`) es una página **estática** con todo el pipeline
corriendo en el navegador del usuario (sin backend, sin Docker, sin VPS, sin Colab):

- Guion/storyboard: `text.pollinations.ai` (gratis, sin API key)
- Imágenes: `image.pollinations.ai` (gratis, sin API key, modelo Flux)
- Animación (Ken Burns zoom/pan) + montaje + mezcla de audio: `@ffmpeg/ffmpeg`
  (FFmpeg.wasm, corre en el navegador vía WebAssembly, cargado desde unpkg)

## Pasos para desplegar (Cloudflare Pages)

1. En el dashboard de Cloudflare → **Workers & Pages → Create → Pages → Connect to Git**.
2. Selecciona el repo `Luimy16/ai-producer`, rama `videoclip-creator`.
3. Build settings:
   - **Framework preset:** None
   - **Build command:** (vacío, no hace falta)
   - **Build output directory:** `gratis`
4. Deploy. Cloudflare te da una URL tipo `https://ai-producer.pages.dev/`
   (o el subpath, según cómo sirvas `gratis/index.html` como raíz).
5. No hay variables de entorno ni secretos que configurar — todo es público
   y gratis del lado del cliente.

## Notas importantes

- **No requiere Colab, GPU, ni que nadie haga clic en nada más** que
  el botón "Crear video" en la propia página. Es la parte 100% automática.
- La animación es tipo "Ken Burns" (zoom/pan sobre la imagen fija), NO
  animación de personajes con movimiento real — eso último (LTX-Video en
  Colab) requiere GPU y sigue siendo manual/con límites de RAM.
- Pensado para canciones cortas (idealmente <60-90s) porque FFmpeg.wasm
  corre en un solo hilo en el navegador del usuario; canciones largas
  tardarán varios minutos en procesar.
- No pude probar las llamadas reales a Pollinations/CDN de FFmpeg.wasm
  desde el entorno donde escribí este código (su red solo permite dominios
  de paquetes/GitHub), pero el código sigue la documentación oficial de
  ambas APIs. Pruébalo en un navegador real al desplegar y avisa en el
  chat si algo falla.

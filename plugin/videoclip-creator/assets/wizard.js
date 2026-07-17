/* VideoClip Creator IA — wizard de 5 pasos (vanilla JS) */
(function () {
  'use strict';
  const app = document.getElementById('vcc-app');
  if (!app || typeof VCC === 'undefined') return;

  const $ = (sel) => app.querySelector(sel);
  const state = { proyecto: null, conceptos: [], concepto: null, escenas: [], polling: null };

  /* ---------- helpers ---------- */
  function error(msg) {
    const e = $('#vcc-error');
    e.textContent = '⚠️ ' + msg;
    e.hidden = false;
    setTimeout(() => { e.hidden = true; }, 8000);
  }
  function irPaso(n) {
    app.querySelectorAll('.vcc-step').forEach(s => s.classList.toggle('activo', +s.dataset.step === n));
    app.querySelectorAll('.vcc-pasos li').forEach(li => {
      li.classList.toggle('activo', +li.dataset.paso === n);
      li.classList.toggle('hecho', +li.dataset.paso < n);
    });
    window.scrollTo({ top: app.offsetTop - 40, behavior: 'smooth' });
  }
  async function api(ruta, datos, metodo = 'POST') {
    const r = await fetch(VCC.rest + 'proxy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': VCC.nonce },
      body: JSON.stringify({ ruta, metodo, datos }),
    });
    const j = await r.json();
    if (!r.ok || j.detail) throw new Error(j.detail || j.error || 'Error ' + r.status);
    return j;
  }
  function btnLoad(btn, on, txtOn, txtOff) {
    btn.disabled = on;
    btn.textContent = on ? txtOn : txtOff;
  }

  /* ---------- PASO 1: subir canción ---------- */
  const inpAudio = $('#vcc-audio'), inpLetra = $('#vcc-letra'), btnSubir = $('#vcc-subir');
  function validarPaso1() { btnSubir.disabled = !(inpAudio.files.length && inpLetra.value.trim().length > 10); }
  inpAudio.addEventListener('change', validarPaso1);
  inpLetra.addEventListener('input', validarPaso1);

  btnSubir.addEventListener('click', async () => {
    btnLoad(btnSubir, true, '⏳ Analizando...', 'Analizar canción →');
    try {
      const fd = new FormData();
      fd.append('audio', inpAudio.files[0]);
      fd.append('letra', inpLetra.value.trim());
      fd.append('formato', $('#vcc-formato').value);
      const r = await fetch(VCC.rest + 'subir-audio', { method: 'POST', headers: { 'X-WP-Nonce': VCC.nonce }, body: fd });
      const j = await r.json();
      if (!r.ok || j.detail) throw new Error(j.detail || j.error || 'Error al subir');
      state.proyecto = j.id;
      $('#vcc-analisis').hidden = false;
      $('#vcc-analisis').innerHTML =
        `✅ <b>Análisis completado</b><br>🥁 BPM: <b>${j.bpm}</b> · ⏱ Duración: <b>${j.duracion}s</b> · 📐 Formato: <b>${j.formato}</b>` +
        (j.bpm === 0 ? '<br><small>(No se pudo detectar el BPM; se usarán escenas de 5s fijas)</small>' : '');
      setTimeout(() => irPaso(2), 900);
    } catch (e) { error(e.message); }
    btnLoad(btnSubir, false, '', 'Analizar canción →');
  });

  /* ---------- PASO 2: conceptos ---------- */
  $('#vcc-gen-conceptos').addEventListener('click', async (ev) => {
    const btn = ev.target;
    btnLoad(btn, true, '⏳ Pensando 3 conceptos...', 'Generar 3 conceptos ✨');
    try {
      const j = await api('proyecto/' + state.proyecto + '/conceptos');
      state.conceptos = j.conceptos;
      const cont = $('#vcc-conceptos');
      cont.innerHTML = '';
      j.conceptos.forEach((c, i) => {
        const card = document.createElement('div');
        card.className = 'vcc-card';
        card.innerHTML = `<h3>${c.nombre}</h3><p>${c.descripcion}</p><p class="vcc-paleta">🎨 ${c.paleta}</p>`;
        card.addEventListener('click', () => {
          state.concepto = i;
          $('#vcc-personaje-desc').value = c.personaje || '';
          irPaso(3);
        });
        cont.appendChild(card);
      });
    } catch (e) { error(e.message); }
    btnLoad(btn, false, '', 'Generar 3 conceptos ✨');
  });

  /* ---------- PASO 3: personaje ---------- */
  $('#vcc-gen-personaje').addEventListener('click', async (ev) => {
    const btn = ev.target;
    btnLoad(btn, true, '⏳ Dibujando (30-60s)...', 'Generar hoja de personaje 🖼');
    try {
      const j = await api('proyecto/' + state.proyecto + '/personaje', { descripcion: $('#vcc-personaje-desc').value, concepto: state.concepto });
      $('#vcc-personaje-out').innerHTML = `<img src="${j.url}" alt="Hoja de personaje" />`;
      $('#vcc-aprobar-personaje').hidden = false;
    } catch (e) { error(e.message); }
    btnLoad(btn, false, '', 'Generar hoja de personaje 🖼');
  });
  $('#vcc-aprobar-personaje').addEventListener('click', () => irPaso(4));

  /* ---------- PASO 4: storyboard ---------- */
  $('#vcc-gen-storyboard').addEventListener('click', async (ev) => {
    const btn = ev.target;
    btnLoad(btn, true, '⏳ Escribiendo el guion...', 'Crear storyboard 🧠');
    try {
      const j = await api('proyecto/' + state.proyecto + '/storyboard', { concepto: state.concepto });
      state.escenas = j.escenas;
      renderStoryboard();
      $('#vcc-generar-todo').hidden = false;
    } catch (e) { error(e.message); }
    btnLoad(btn, false, '', 'Crear storyboard 🧠');
  });

  function renderStoryboard() {
    const cont = $('#vcc-storyboard');
    cont.innerHTML = '';
    state.escenas.forEach((esc, i) => {
      const div = document.createElement('div');
      div.className = 'vcc-escena';
      div.innerHTML =
        `<div class="vcc-escena-head"><b>Escena ${i + 1}</b> · ${esc.seccion || ''} · ${esc.duracion}s` +
        (esc.lipsync ? ' · 💬 lipsync' : '') + ` <span class="vcc-estado" id="vcc-est-${i}">⬜</span></div>` +
        `<textarea data-i="${i}" rows="2">${esc.prompt}</textarea>` +
        `<div class="vcc-escena-media" id="vcc-media-${i}"></div>`;
      cont.appendChild(div);
    });
    cont.querySelectorAll('textarea').forEach(t =>
      t.addEventListener('input', () => { state.escenas[+t.dataset.i].prompt = t.value; }));
  }

  async function generarEscena(i) {
    const est = $('#vcc-est-' + i), media = $('#vcc-media-' + i);
    try {
      est.textContent = '🖼 imagen...';
      const img = await api(`proyecto/${state.proyecto}/escenas/${i}/imagen`, { prompt: state.escenas[i].prompt });
      media.innerHTML = `<img src="${img.url}" />`;
      est.textContent = '🎬 video (3-8 min)...';
      const vid = await api(`proyecto/${state.proyecto}/escenas/${i}/video`, { prompt: state.escenas[i].prompt, duracion: state.escenas[i].duracion });
      if (state.escenas[i].lipsync) {
        est.textContent = '💬 lipsync...';
        await api(`proyecto/${state.proyecto}/escenas/${i}/lipsync`);
      }
      media.innerHTML = `<video src="${vid.url}?t=${Date.now()}" controls muted loop></video>`;
      est.textContent = '✅';
    } catch (e) {
      est.textContent = '❌';
      throw new Error('Escena ' + (i + 1) + ': ' + e.message);
    }
  }

  $('#vcc-generar-todo').addEventListener('click', async (ev) => {
    const btn = ev.target;
    btnLoad(btn, true, '⏳ Generando...', '🎬 Generar todas las escenas');
    $('#vcc-progreso').hidden = false;
    const total = state.escenas.length;
    for (let i = 0; i < total; i++) {
      $('#vcc-progreso-txt').textContent = `Escena ${i + 1} de ${total}...`;
      $('#vcc-barra-fill').style.width = ((i / total) * 100) + '%';
      try { await generarEscena(i); }
      catch (e) { error(e.message); break; }
    }
    $('#vcc-barra-fill').style.width = '100%';
    $('#vcc-progreso-txt').textContent = '✅ Escenas listas';
    btnLoad(btn, false, '', '🎬 Generar todas las escenas');
    setTimeout(() => irPaso(5), 800);
  });

  /* ---------- PASO 5: ensamblar ---------- */
  $('#vcc-ensamblar').addEventListener('click', async (ev) => {
    const btn = ev.target;
    btnLoad(btn, true, '⏳ Ensamblando con FFmpeg...', 'Ensamblar videoclip final 🎬');
    try {
      const j = await api('proyecto/' + state.proyecto + '/ensamblar');
      $('#vcc-final').innerHTML =
        `<video src="${j.url}?t=${Date.now()}" controls style="width:100%"></video>
         <a class="vcc-btn vcc-btn-ok" href="${j.url}" download="mi-videoclip.mp4">⬇ Descargar videoclip</a>`;
    } catch (e) { error(e.message); }
    btnLoad(btn, false, '', 'Ensamblar videoclip final 🎬');
  });
})();

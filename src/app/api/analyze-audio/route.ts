export const runtime = "edge";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const audioFile = formData.get("audio") as File | null;
    const genre = formData.get("genre") as string || "";
    const duration = formData.get("duration") as string || "";

    const apiKey = process.env.OPENROUTER_API_KEY || "";
    if (!apiKey) {
      return Response.json({ error: "Motor IA no configurado" }, { status: 500 });
    }

    // Build analysis prompt based on what we have
    let analysisPrompt = `Analiza la siguiente pista musical para producción de videoclip.\n`;

    if (audioFile) {
      analysisPrompt += `\nSe ha subido un archivo de audio: "${audioFile.name}" (${(audioFile.size / 1024 / 1024).toFixed(1)} MB).\n`;
    }
    if (genre) analysisPrompt += `\nGénero musical indicado: ${genre}`;
    if (duration) analysisPrompt += `\nDuración aproximada: ${duration}`;

    analysisPrompt += `\n\nProporciona un análisis profesional con la siguiente estructura:
1. **Género y Estilo**: Identifica el género musical y estilo
2. **BPM y Ritmo**: Estima el tempo y patrón rítmico
3. **Estructura**: Identifica intro, verso, coro, puente, outro
4. **Paleta Visual Recomendada**: Colores, iluminación y atmósfera
5. **Concepto Visual**: 3 ideas de concepto para el videoclip
6. **Planos Sugeridos**: Tipos de planos y movimientos de cámara recomendados

Responde en español profesional.`;

    const payload = {
      model: "openrouter/auto",
      messages: [
        {
          role: "system",
          content: "Eres un director de videoclips y productor musical experto. Analizas pistas de audio y propones dirección visual profesional. Responde en español."
        },
        { role: "user", content: analysisPrompt },
      ],
      temperature: 0.8,
      max_tokens: 1500,
    };

    const res = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "HTTP-Referer": "https://ai-producer.pages.dev",
        "X-Title": "AI Producer Suite",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      return Response.json({ error: `Error del motor IA (${res.status})` }, { status: 502 });
    }

    const data = await res.json();
    const analysis = data.choices?.[0]?.message?.content || "";

    return Response.json({ success: true, analysis, usage: data.usage });
  } catch (e: any) {
    return Response.json({ error: "Error al analizar el audio" }, { status: 500 });
  }
}

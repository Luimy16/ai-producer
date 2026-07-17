export const runtime = "edge";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export async function POST(req: Request) {
  try {
    const { genre, concept, duration, style, scriptNotes } = await req.json();
    const apiKey = process.env.OPENROUTER_API_KEY || "";

    if (!apiKey) {
      return Response.json({ error: "Motor IA no configurado" }, { status: 500 });
    }

    const videoPrompt = `Crea un guion técnico profesional completo para un videoclip musical con las siguientes especificaciones:

${genre ? `Género Musical: ${genre}` : ""}
${concept ? `Concepto Visual: ${concept}` : ""}
${duration ? `Duración: ${duration}` : ""}
${style ? `Estilo Visual: ${style}` : ""}
${scriptNotes ? `Notas adicionales: ${scriptNotes}` : ""}

EL GUION DEBE INCLUIR:
1. **Ficha Técnica**: Título propuesto, género, duración, estilo visual, paleta de colores
2. **Estructura de Escenas** (mínimo 5 escenas, cada una con):
   - Número y nombre de escena
   - Timecode (inicio - fin)
   - Tipo de plano (primer plano, plano medio, panorámico, etc.)
   - Movimiento de cámara (travelling, steady, drone, etc.)
   - Descripción visual detallada
   - Iluminación y atmósfera
   - Elementos en escena
3. **Dirección de Arte**: Vestuario, maquillaje, utilería
4. **Post-producción**: Efectos visuales sugeridos, etalonaje, transiciones

Formato profesional, enumerado, en español. Sé extremadamente detallado y creativo.`;

    const payload = {
      model: "openrouter/auto",
      messages: [
        {
          role: "system",
          content: "Eres un director de cine y videoclips de talla mundial. Creas guiones técnicos profesionales con máximo detalle cinematográfico. Responde en español."
        },
        { role: "user", content: videoPrompt },
      ],
      temperature: 0.85,
      max_tokens: 2500,
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
    const script = data.choices?.[0]?.message?.content || "";

    return Response.json({
      success: true,
      script,
      videoUrl: null, // Real video generation via external service would go here
      usage: data.usage,
    });
  } catch (e: any) {
    return Response.json({ error: "Error al crear el video" }, { status: 500 });
  }
}

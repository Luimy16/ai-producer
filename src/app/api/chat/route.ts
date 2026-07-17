export const runtime = "edge";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    const apiKey = process.env.OPENROUTER_API_KEY || "";

    if (!apiKey) {
      return Response.json({ error: "Motor IA no configurado" }, { status: 500 });
    }

    const systemMsg = `Eres el Agente Productor de AI Producer Suite, una plataforma profesional de producción audiovisual con IA.

TUS CAPACIDADES:
- Crear guiones técnicos para videoclips (escena por escena, con dirección de cámara, iluminación y timing)
- Diseñar prompts detallados para generación de imágenes 8K
- Analizar conceptos musicales y proponer dirección visual
- Crear storyboards cinematográficos
- Asesorar en producción audiovisual profesional

REGLAS:
- Responde SIEMPRE en español profesional
- Cuando te pidan crear un video, genera un guion técnico completo con: escenas numeradas, descripción visual, tipo de plano, iluminación, duración estimada
- Sé creativo, detallado y ejecutivo
- No menciones que eres una IA, actúa como un director de producción real
- No uses markdown excesivo, sé directo y profesional`;

    const payload = {
      model: "openrouter/auto",
      messages: [
        { role: "system", content: systemMsg },
        ...(messages || []),
      ],
      temperature: 0.8,
      max_tokens: 2000,
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
      const errText = await res.text();
      return Response.json({ error: `Error del motor IA (${res.status})` }, { status: 502 });
    }

    const data = await res.json();
    const reply = data.choices?.[0]?.message?.content || "Sin respuesta del modelo.";

    return Response.json({ success: true, reply, usage: data.usage });
  } catch (e: any) {
    return Response.json({ error: "Error de conexión con el motor IA" }, { status: 500 });
  }
}

"use client";

import React, { useState, useRef } from "react";
import {
  Sparkles, Upload, Music, Film, Wand2, Play, Download,
  Bot, Send, X, Loader2, FileAudio, Camera, MessageSquare,
  Lightbulb, Palette, Timer
} from "lucide-react";

// ==================== CHATBOT COMPONENT ====================
function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([
    { role: "assistant", text: "¡Hola! Soy tu Productor IA. Puedo crear guiones para videoclips, analizar tu música, y generar conceptos visuales. ¿Qué proyecto trabajamos hoy?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMsg = async (text?: string) => {
    const msg = text || input;
    if (!msg.trim() || loading) return;

    const updated = [...messages, { role: "user", text: msg }];
    setMessages(updated);
    if (!text) setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: updated.map(m => ({ role: m.role, content: m.text })) }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.reply || data.error || "Error de conexión" }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", text: "Lo siento, hubo un error. Intenta de nuevo en un momento." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {!isOpen ? (
        <button onClick={() => setIsOpen(true)} className="flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-[#1a1f35] to-[#0d1225] border-2 border-[#d4af37]/60 text-[#d4af37] rounded-full shadow-2xl hover:scale-105 transition-all">
          <Bot className="w-5 h-5" />
          <span className="font-semibold text-sm">Productor IA</span>
        </button>
      ) : (
        <div className="w-[380px] h-[520px] bg-[#0d1225] border border-[#d4af37]/40 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          <div className="bg-[#1a1f35] px-4 py-3 flex items-center justify-between border-b border-[#243044]">
            <div className="flex items-center gap-2.5">
              <Bot className="w-5 h-5 text-[#d4af37]" />
              <span className="font-bold text-sm">Productor IA</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2.5 text-xs">
            {messages.map((m, i) => (
              <div key={i} className={`p-2.5 rounded-xl max-w-[85%] ${m.role === "user" ? "bg-[#d4af37]/20 border border-[#d4af37]/30 ml-auto" : "bg-[#1a1f35] border border-[#243044]"}`}>
                <div className="whitespace-pre-wrap leading-relaxed">{m.text}</div>
              </div>
            ))}
            {loading && <div className="text-[#d4af37] text-xs flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Procesando...</div>}
          </div>
          <form onSubmit={e => { e.preventDefault(); sendMsg(); }} className="p-3 bg-[#1a1f35] flex gap-2 border-t border-[#243044]">
            <input value={input} onChange={e => setInput(e.target.value)} placeholder="Escribe tu consulta..." className="flex-1 bg-[#0d1225] border border-[#243044] focus:border-[#d4af37] text-slate-100 text-xs rounded-xl px-3 py-2.5 outline-none" />
            <button type="submit" disabled={!input.trim() || loading} className="p-2.5 bg-[#d4af37] text-black rounded-xl font-bold disabled:opacity-40"><Send className="w-4 h-4" /></button>
          </form>
        </div>
      )}
    </div>
  );
}

// ==================== MAIN APP ====================
export default function Home() {
  const [activeTab, setActiveTab] = useState<"videoclip" | "chat">("videoclip");

  // Video Creator State
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [genre, setGenre] = useState("");
  const [concept, setConcept] = useState("");
  const [duration, setDuration] = useState("3:00");
  const [style, setStyle] = useState("Cinematográfico");
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("");
  const [result, setResult] = useState<{ analysis?: string; script?: string } | null>(null);
  const [error, setError] = useState("");

  const handleAudioUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setAudioFile(file);
  };

  const handleCreateVideo = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      // Step 1: Analyze audio (if uploaded)
      if (audioFile) {
        setPhase("Analizando audio con IA...");
        const fd = new FormData();
        fd.append("audio", audioFile);
        fd.append("genre", genre);
        fd.append("duration", duration);

        const analysisRes = await fetch("/api/analyze-audio", { method: "POST", body: fd });
        const analysisData = await analysisRes.json();

        if (!analysisData.success) {
          setError(analysisData.error || "Error al analizar el audio");
          setLoading(false);
          return;
        }

        // Use AI analysis for concept
        if (analysisData.analysis && !concept) {
          setConcept(analysisData.analysis.split("\n")[0] || "");
        }
      }

      // Step 2: Create video script
      setPhase("Creando guion técnico del videoclip...");

      const videoRes = await fetch("/api/create-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ genre, concept, duration, style, scriptNotes: "" }),
      });

      const videoData = await videoRes.json();

      if (!videoData.success) {
        setError(videoData.error || "Error al crear el video");
        setLoading(false);
        return;
      }

      setPhase("¡Videoclip creado con éxito!");
      setResult({ script: videoData.script });

      // Step 3: Re-analyze if we already did it
      if (audioFile) {
        const fd2 = new FormData();
        fd2.append("audio", audioFile);
        fd2.append("genre", genre);
        fd2.append("duration", duration);
        const aRes = await fetch("/api/analyze-audio", { method: "POST", body: fd2 });
        const aData = await aRes.json();
        if (aData.success) {
          setResult(prev => ({ ...prev, analysis: aData.analysis }));
        }
      }
    } catch (e) {
      setError("Error de conexión. Revisa tu internet e inténtalo de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080b14] text-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-[#080b14]/90 backdrop-blur-xl border-b border-[#1a2035]">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#d4af37] to-[#3b82f6] p-0.5">
              <div className="w-full h-full bg-[#080b14] rounded-[10px] flex items-center justify-center text-[#d4af37]">
                <Wand2 className="w-4 h-4" />
              </div>
            </div>
            <span className="font-bold text-lg tracking-tight">AI PRODUCER</span>
          </div>

          <nav className="flex bg-[#0d1225] p-1 rounded-xl border border-[#1a2035]">
            <button onClick={() => setActiveTab("videoclip")} className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === "videoclip" ? "bg-[#d4af37] text-black" : "text-slate-400 hover:text-white"}`}>
              <Film className="w-3.5 h-3.5 inline mr-1.5" />
              Crear Videoclip
            </button>
            <button onClick={() => setActiveTab("chat")} className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${activeTab === "chat" ? "bg-[#d4af37] text-black" : "text-slate-400 hover:text-white"}`}>
              <MessageSquare className="w-3.5 h-3.5 inline mr-1.5" />
              Chat con IA
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Hero */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#d4af37]/10 border border-[#d4af37]/30 text-[#d4af37] text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Motor de Producción Neural
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">
            Crea Videoclips con{" "}
            <span className="bg-gradient-to-r from-[#d4af37] to-[#f5e6a3] bg-clip-text text-transparent">Inteligencia Artificial</span>
          </h1>
          <p className="mt-3 text-sm text-slate-400 max-w-xl mx-auto">
            Sube tu audio, la IA analiza el ritmo y género, y genera un guion técnico profesional completo para tu videoclip.
          </p>
        </div>

        {activeTab === "videoclip" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Controls */}
            <div className="bg-[#0d1225] border border-[#1a2035] rounded-2xl p-5 space-y-4">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Music className="w-4 h-4 text-[#d4af37]" />
                Configura tu Videoclip
              </h3>

              {/* Audio Upload */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-2">Audio (MP3, WAV)</label>
                <label className="flex flex-col items-center gap-2 p-4 border-2 border-dashed border-[#1a2035] hover:border-[#d4af37]/50 rounded-xl cursor-pointer bg-[#080b14]/50 transition-colors">
                  <input type="file" accept="audio/*" onChange={handleAudioUpload} className="hidden" />
                  {audioFile ? (
                    <div className="text-center">
                      <FileAudio className="w-8 h-8 text-[#d4af37] mx-auto mb-1" />
                      <span className="text-xs text-[#d4af37] font-semibold">{audioFile.name}</span>
                      <span className="text-[10px] text-slate-500 block">{(audioFile.size / 1024 / 1024).toFixed(1)} MB</span>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-8 h-8 text-slate-500" />
                      <span className="text-xs text-slate-400">Subir archivo de audio</span>
                    </>
                  )}
                </label>
              </div>

              {/* Genre */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Género Musical</label>
                <input
                  type="text"
                  value={genre}
                  onChange={e => setGenre(e.target.value)}
                  placeholder="Ej: Reggaetón, Synthwave, Pop..."
                  className="w-full bg-[#080b14] border border-[#1a2035] focus:border-[#d4af37] text-slate-100 text-xs rounded-xl px-3 py-2.5 outline-none"
                />
              </div>

              {/* Concept */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
                  <Lightbulb className="w-3.5 h-3.5 text-[#d4af37]" />
                  Concepto Visual (opcional)
                </label>
                <textarea
                  value={concept}
                  onChange={e => setConcept(e.target.value)}
                  rows={3}
                  placeholder="Describe el concepto visual que imaginas. Si dejas vacío, la IA lo creará por ti."
                  className="w-full bg-[#080b14] border border-[#1a2035] focus:border-[#d4af37] text-slate-100 text-xs rounded-xl px-3 py-2.5 outline-none resize-none"
                />
              </div>

              {/* Duration */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
                  <Timer className="w-3.5 h-3.5 text-[#d4af37]" />
                  Duración Aproximada
                </label>
                <input
                  type="text"
                  value={duration}
                  onChange={e => setDuration(e.target.value)}
                  placeholder="3:00"
                  className="w-full bg-[#080b14] border border-[#1a2035] focus:border-[#d4af37] text-slate-100 text-xs rounded-xl px-3 py-2.5 outline-none"
                />
              </div>

              {/* Style */}
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5 flex items-center gap-1.5">
                  <Palette className="w-3.5 h-3.5 text-[#d4af37]" />
                  Estilo Visual
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {["Cinematográfico", "Cyberpunk", "Minimalista", "Retro/VHS", "Animación 3D", "Blanco y Negro"].map(s => (
                    <button
                      key={s}
                      onClick={() => setStyle(s)}
                      className={`text-xs py-2 rounded-lg border transition-all ${style === s ? "bg-[#d4af37]/20 border-[#d4af37] text-[#d4af37] font-bold" : "bg-[#080b14] border-[#1a2035] text-slate-400"}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Create Button */}
              <button
                onClick={handleCreateVideo}
                disabled={loading}
                className="w-full py-3.5 bg-gradient-to-r from-[#d4af37] to-[#b8922a] hover:from-[#e5bf48] hover:to-[#c49216] text-black font-extrabold text-sm uppercase tracking-wider rounded-xl shadow-xl hover:scale-[1.02] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {phase || "Procesando..."}
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    Crear Videoclip con IA
                  </>
                )}
              </button>
            </div>

            {/* Right Results */}
            <div className="lg:col-span-2 bg-[#0d1225] border border-[#1a2035] rounded-2xl p-5 min-h-[500px]">
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-sm text-red-300 mb-4">
                  {error}
                </div>
              )}

              {result ? (
                <div className="space-y-6">
                  {result.analysis && (
                    <div>
                      <h3 className="font-bold text-[#d4af37] text-sm flex items-center gap-2 mb-3">
                        <Music className="w-4 h-4" />
                        Análisis del Audio
                      </h3>
                      <div className="bg-[#080b14] border border-[#1a2035] rounded-xl p-4 text-xs leading-relaxed whitespace-pre-wrap text-slate-200">
                        {result.analysis}
                      </div>
                    </div>
                  )}

                  {result.script && (
                    <div>
                      <h3 className="font-bold text-[#d4af37] text-sm flex items-center gap-2 mb-3">
                        <Film className="w-4 h-4" />
                        Guion Técnico del Videoclip
                      </h3>
                      <div className="bg-[#080b14] border border-[#d4af37]/30 rounded-xl p-4 text-xs leading-relaxed whitespace-pre-wrap text-slate-200 max-h-[600px] overflow-y-auto">
                        {result.script}
                      </div>

                      <button
                        onClick={() => {
                          const blob = new Blob([result.script || ""], { type: "text/plain" });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = "guion-videoclip.txt";
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                        className="mt-3 flex items-center gap-1.5 px-4 py-2 bg-[#d4af37] text-black font-bold text-xs rounded-xl hover:bg-[#e5bf48] transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Descargar Guion (TXT)
                      </button>
                    </div>
                  )}
                </div>
              ) : !loading ? (
                <div className="h-full flex flex-col items-center justify-center text-center py-16">
                  <div className="w-16 h-16 rounded-2xl bg-[#d4af37]/10 border border-[#d4af37]/30 flex items-center justify-center text-[#d4af37] mb-4">
                    <Film className="w-8 h-8" />
                  </div>
                  <h3 className="font-bold text-slate-300">Tu videoclip aparecerá aquí</h3>
                  <p className="text-xs text-slate-500 mt-2 max-w-sm">
                    Sube tu audio, configura el género y estilo, y la IA generará un guion técnico completo escena por escena.
                  </p>
                </div>
              ) : null}
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div className="max-w-2xl mx-auto bg-[#0d1225] border border-[#1a2035] rounded-2xl p-5">
            <h3 className="font-bold text-sm flex items-center gap-2 mb-4">
              <MessageSquare className="w-4 h-4 text-[#d4af37]" />
              Chat Directo con la IA
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Pregúntale a la IA lo que necesites: ideas para videoclips, guiones, análisis de conceptos musicales, dirección de arte. Todo en tiempo real.
            </p>
            <ChatInline />
          </div>
        )}
      </main>

      {/* Floating Chatbot */}
      <Chatbot />

      {/* Footer */}
      <footer className="border-t border-[#1a2035] py-6 text-xs text-slate-500 text-center">
        AI Producer Suite — Motor de Producción Audiovisual con Inteligencia Artificial
      </footer>
    </div>
  );
}

// Inline chat for the dedicated chat tab
function ChatInline() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMsg = async () => {
    if (!input.trim() || loading) return;
    const updated = [...messages, { role: "user", text: input }];
    setMessages(updated);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: updated.map(m => ({ role: m.role, content: m.text })) }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.reply || data.error || "Error" }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", text: "Error de conexión." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="bg-[#080b14] border border-[#1a2035] rounded-xl p-3 min-h-[300px] max-h-[400px] overflow-y-auto space-y-2 text-xs">
        {messages.length === 0 && (
          <p className="text-slate-500 text-center py-12">
            Escribe tu primer mensaje para empezar...
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`p-2.5 rounded-xl max-w-[85%] ${m.role === "user" ? "bg-[#d4af37]/20 border border-[#d4af37]/30 ml-auto" : "bg-[#0d1225] border border-[#1a2035]"}`}>
            <div className="whitespace-pre-wrap leading-relaxed">{m.text}</div>
          </div>
        ))}
        {loading && <div className="text-[#d4af37] text-xs flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Pensando...</div>}
      </div>
      <form onSubmit={e => { e.preventDefault(); sendMsg(); }} className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ej: Crea un guion para un videoclip de reggaetón futurista..."
          className="flex-1 bg-[#080b14] border border-[#1a2035] focus:border-[#d4af37] text-slate-100 text-xs rounded-xl px-3 py-2.5 outline-none"
        />
        <button type="submit" disabled={!input.trim() || loading} className="px-4 py-2.5 bg-[#d4af37] text-black font-bold text-xs rounded-xl disabled:opacity-40">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Producer Suite — Producción Audiovisual con IA",
  description: "Crea videoclips, guiones y contenido audiovisual profesional con inteligencia artificial.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body className="bg-[#080b14] text-slate-100 min-h-screen">{children}</body>
    </html>
  );
}

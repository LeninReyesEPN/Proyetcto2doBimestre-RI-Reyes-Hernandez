import type { Metadata } from "next"
import { Josefin_Sans, Geist_Mono } from "next/font/google"
import { TooltipProvider } from "@/components/ui/tooltip"
import "./globals.css"

const josefinSans = Josefin_Sans({
  variable: "--font-josefin-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Gemini AI - Chat Conversacional Premium",
  description: "Interfaz conversacional de alta fidelidad con diseño de Glassmorfismo y Minimalismo, construida con React, Next.js y prompt-kit.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="es"
      className={`${josefinSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 dark:bg-zinc-950">
        <TooltipProvider delay={400}>
          {children}
        </TooltipProvider>
      </body>
    </html>
  )
}

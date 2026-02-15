import type { Metadata } from "next"
import "./globals.css"
import { QueryProvider } from "@/components/providers"

export const metadata: Metadata = {
  title: "Vectory - Vector Database",
  description: "High-performance vector database with built-in ingestion pipelines",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}

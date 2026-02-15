"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Database, Home, Upload, Settings, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/collections", label: "Collections", icon: Database },
  { href: "/ingestion", label: "Ingestion", icon: Upload },
  { href: "/settings", label: "Settings", icon: Settings },
]

interface SidebarProps {
  mobile?: boolean
  onClose?: () => void
}

export function Sidebar({ mobile, onClose }: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      className={cn(
        "flex w-64 flex-col border-r bg-card h-full",
        mobile ? "flex" : "hidden md:flex",
      )}
    >
      <div className="flex h-16 items-center justify-between border-b px-6">
        <Link href="/" className="flex items-center space-x-2" onClick={onClose}>
          <Database className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">Vectory</span>
        </Link>
        {mobile && onClose && (
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={cn(
                "flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <item.icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">Vectory v1.0.0</p>
      </div>
    </aside>
  )
}

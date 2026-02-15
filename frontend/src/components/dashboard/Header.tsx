"use client"

import { useState } from "react"
import { LogOut, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth-context"

interface HeaderProps {
  title: string
  onMenuToggle?: () => void
}

export function Header({ title, onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth()
  const [showMenu, setShowMenu] = useState(false)

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-4 md:px-6">
      <div className="flex items-center space-x-3">
        {onMenuToggle && (
          <Button variant="ghost" size="icon" className="md:hidden" onClick={onMenuToggle}>
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <h1 className="text-xl font-semibold">{title}</h1>
      </div>
      <div className="relative">
        <button
          onClick={() => setShowMenu(!showMenu)}
          className="flex items-center space-x-2 rounded-md px-3 py-2 text-sm hover:bg-muted transition-colors"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-medium">
            {user?.name ? user.name[0].toUpperCase() : user?.email?.[0]?.toUpperCase() || "U"}
          </div>
          <span className="hidden sm:inline text-sm font-medium">
            {user?.name || user?.email || "User"}
          </span>
        </button>
        {showMenu && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
            <div className="absolute right-0 top-full z-50 mt-1 w-56 rounded-md border bg-card shadow-lg">
              <div className="p-3 border-b">
                <p className="text-sm font-medium">{user?.name || "User"}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <div className="p-1">
                <button
                  onClick={() => {
                    setShowMenu(false)
                    logout()
                  }}
                  className="flex w-full items-center space-x-2 rounded-sm px-3 py-2 text-sm text-destructive hover:bg-muted transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </header>
  )
}

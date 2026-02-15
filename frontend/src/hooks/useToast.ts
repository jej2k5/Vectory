"use client"

import { useCallback, useState } from "react"

export interface ToastMessage {
  id: string
  title: string
  description?: string
  variant?: "default" | "destructive" | "success"
}

let toastCounter = 0

export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toast = useCallback(
    (msg: Omit<ToastMessage, "id">) => {
      const id = String(++toastCounter)
      setToasts((prev) => [...prev, { ...msg, id }])
      return id
    },
    [],
  )

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return { toasts, toast, dismiss }
}

// Global toast singleton so it can be used outside React components
type ToastFn = (msg: Omit<ToastMessage, "id">) => void
type DismissFn = (id: string) => void

let globalToast: ToastFn | null = null
let globalDismiss: DismissFn | null = null

export function registerToast(toastFn: ToastFn, dismissFn: DismissFn) {
  globalToast = toastFn
  globalDismiss = dismissFn
}

export function showToast(msg: Omit<ToastMessage, "id">) {
  if (globalToast) globalToast(msg)
}

export function dismissToast(id: string) {
  if (globalDismiss) globalDismiss(id)
}

"use client"

import { type ReactNode, useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface InteractiveButtonProps {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: "default" | "outline" | "ghost"
  size?: "default" | "sm" | "lg"
  className?: string
}

export default function InteractiveButton({
  children,
  onClick,
  disabled = false,
  variant = "default",
  size = "default",
  className,
}: InteractiveButtonProps) {
  const [isClicked, setIsClicked] = useState(false)

  const handleClick = () => {
    if (disabled) return

    setIsClicked(true)
    setTimeout(() => setIsClicked(false), 200)

    if (onClick) {
      onClick()
    }
  }

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        "relative overflow-hidden transition-all duration-300 transform hover:scale-105 active:scale-95",
        isClicked && "animate-pulse",
        !disabled && "hover:shadow-lg hover:shadow-current/25",
        className,
      )}
    >
      {/* Ripple effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700"></div>

      {/* Button content */}
      <span className="relative z-10 flex items-center justify-center">{children}</span>
    </Button>
  )
}

"use client"

import { type ReactNode, useEffect, useState } from "react"
import { Card } from "@/components/ui/card"

interface GlowingCardProps {
  children: ReactNode
  delay?: number
}

export default function GlowingCard({ children, delay = 0 }: GlowingCardProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true)
    }, delay * 1000)

    return () => clearTimeout(timer)
  }, [delay])

  return (
    <div
      className={`group relative transition-all duration-700 transform ${
        isVisible ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
      }`}
    >
      {/* Glowing background */}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 rounded-xl blur opacity-30 group-hover:opacity-60 transition duration-300"></div>

      {/* Card content */}
      <Card className="relative bg-slate-900/90 backdrop-blur-xl border-slate-700/50 hover:border-cyan-400/50 transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-cyan-500/25">
        {children}
      </Card>
    </div>
  )
}

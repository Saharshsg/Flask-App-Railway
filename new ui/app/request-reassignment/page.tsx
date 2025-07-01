"use client"

import type React from "react"

import { useState } from "react"
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ArrowLeft, Send, Calendar } from "lucide-react"
import { useRouter } from "next/navigation"
import ParticleBackground from "../components/particle-background"
import FuturisticNavbar from "../components/futuristic-navbar"
import GlowingCard from "../components/glowing-card"
import InteractiveButton from "../components/interactive-button"

export default function RequestReassignment() {
  const [reason, setReason] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const router = useRouter()

  const scheduleEntry = {
    date: new Date("2024-01-16"),
    day: "Tuesday",
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000))

    setIsSubmitting(false)
    router.push("/")
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10">
        <FuturisticNavbar />

        <div className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
                Request Reassignment
              </h1>
              <div className="w-24 h-1 bg-gradient-to-r from-cyan-400 to-purple-400 mx-auto rounded-full"></div>
            </div>

            <GlowingCard>
              <CardHeader className="pb-6">
                <CardTitle className="text-2xl font-bold text-white flex items-center gap-3">
                  <Calendar className="w-6 h-6 text-cyan-400" />
                  Reassignment Request
                </CardTitle>
                <p className="text-gray-300 text-lg">
                  You are requesting a reassignment for your spot on{" "}
                  <span className="text-cyan-400 font-semibold">
                    {scheduleEntry.date.toLocaleDateString("en-US", {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </p>
              </CardHeader>

              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="reason" className="block text-sm font-medium text-gray-300 mb-2">
                      Reason for Request
                    </label>
                    <Textarea
                      id="reason"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Please provide a brief reason for your request..."
                      rows={4}
                      className="w-full bg-slate-800/50 border-slate-600/50 text-white placeholder-gray-400 focus:border-cyan-400/50 focus:ring-cyan-400/25 resize-none"
                      required
                    />
                  </div>

                  <div className="flex gap-4 pt-4">
                    <InteractiveButton
                      type="submit"
                      disabled={isSubmitting || !reason.trim()}
                      className="flex-1 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 disabled:opacity-50"
                    >
                      {isSubmitting ? (
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                          Submitting...
                        </div>
                      ) : (
                        <>
                          <Send className="w-4 h-4 mr-2" />
                          Submit Request
                        </>
                      )}
                    </InteractiveButton>

                    <InteractiveButton
                      type="button"
                      variant="outline"
                      onClick={() => router.push("/")}
                      className="border-gray-500/50 text-gray-400 hover:bg-gray-500/20"
                    >
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      Cancel
                    </InteractiveButton>
                  </div>
                </form>
              </CardContent>
            </GlowingCard>
          </div>
        </div>
      </div>
    </div>
  )
}

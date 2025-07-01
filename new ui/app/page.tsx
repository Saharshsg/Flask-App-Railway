"use client"

import { useState } from "react"
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Users, Calendar, Zap, ArrowRight, Shuffle, X, Check } from "lucide-react"
import ParticleBackground from "./components/particle-background"
import FuturisticNavbar from "./components/futuristic-navbar"
import GlowingCard from "./components/glowing-card"
import InteractiveButton from "./components/interactive-button"

// Mock data structure matching the original functionality
const OFFICE_CAPACITY = 3

interface ScheduleEntry {
  id: string
  date: Date
  day: string
  slots_filled: number
  attendees: string[]
  is_past: boolean
  user_choice?: {
    status: "Yes" | "No"
    was_auto_assigned: boolean
    is_available: boolean
  }
}

const mockScheduleData: ScheduleEntry[] = [
  {
    id: "1",
    date: new Date("2024-01-15"),
    day: "Monday",
    slots_filled: 2,
    attendees: ["Alice Johnson", "Bob Smith"],
    is_past: false,
    user_choice: { status: "No", was_auto_assigned: false, is_available: true },
  },
  {
    id: "2",
    date: new Date("2024-01-16"),
    day: "Tuesday",
    slots_filled: 3,
    attendees: ["Charlie Brown", "Diana Prince", "Eve Wilson"],
    is_past: false,
    user_choice: { status: "Yes", was_auto_assigned: true, is_available: false },
  },
  {
    id: "3",
    date: new Date("2024-01-17"),
    day: "Wednesday",
    slots_filled: 1,
    attendees: ["Frank Miller"],
    is_past: false,
    user_choice: { status: "No", was_auto_assigned: false, is_available: false },
  },
  {
    id: "4",
    date: new Date("2024-01-18"),
    day: "Thursday",
    slots_filled: 0,
    attendees: [],
    is_past: false,
  },
  {
    id: "5",
    date: new Date("2024-01-19"),
    day: "Friday",
    slots_filled: 2,
    attendees: ["Grace Lee", "Henry Ford"],
    is_past: false,
    user_choice: { status: "No", was_auto_assigned: false, is_available: true },
  },
]

export default function FuturisticOfficePlanner() {
  const [scheduleData, setScheduleData] = useState<ScheduleEntry[]>(mockScheduleData)
  const [selectedMeal, setSelectedMeal] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)

  const handleAttendanceChange = async (entryId: string, status: "Yes" | "No", mealPreference?: string) => {
    setIsLoading(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    setScheduleData((prev) =>
      prev.map((entry) => {
        if (entry.id === entryId) {
          const updatedEntry = { ...entry }

          if (status === "Yes") {
            updatedEntry.slots_filled = Math.min(updatedEntry.slots_filled + 1, OFFICE_CAPACITY)
            updatedEntry.attendees = [...updatedEntry.attendees, "You"]
            updatedEntry.user_choice = { status: "Yes", was_auto_assigned: false, is_available: false }
          } else {
            if (updatedEntry.user_choice?.status === "Yes") {
              updatedEntry.slots_filled = Math.max(updatedEntry.slots_filled - 1, 0)
              updatedEntry.attendees = updatedEntry.attendees.filter((name) => name !== "You")
            }
            updatedEntry.user_choice = { status: "No", was_auto_assigned: false, is_available: false }
          }

          return updatedEntry
        }
        return entry
      }),
    )

    setIsLoading(false)
  }

  const toggleAvailability = async (entryId: string) => {
    setIsLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 500))

    setScheduleData((prev) =>
      prev.map((entry) => {
        if (entry.id === entryId && entry.user_choice) {
          return {
            ...entry,
            user_choice: {
              ...entry.user_choice,
              is_available: !entry.user_choice.is_available,
            },
          }
        }
        return entry
      }),
    )

    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      <ParticleBackground />

      <div className="relative z-10">
        <FuturisticNavbar />

        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-12">
            <h1 className="text-6xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4 animate-pulse">
              Weekly Office Schedule
            </h1>
            <div className="w-32 h-1 bg-gradient-to-r from-cyan-400 to-purple-400 mx-auto rounded-full"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {scheduleData.map((entry, index) => (
              <GlowingCard key={entry.id} delay={index * 0.1}>
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-2xl font-bold text-white flex items-center gap-2">
                      <Calendar className="w-6 h-6 text-cyan-400" />
                      {entry.day}
                    </CardTitle>
                    <div className="text-sm text-gray-400">
                      {entry.date.toLocaleDateString("en-US", { month: "long", day: "numeric" })}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    <Users className="w-4 h-4 text-purple-400" />
                    <Badge
                      variant={entry.slots_filled >= OFFICE_CAPACITY ? "destructive" : "default"}
                      className={`${
                        entry.slots_filled >= OFFICE_CAPACITY
                          ? "bg-red-500/20 text-red-400 border-red-500/50"
                          : "bg-green-500/20 text-green-400 border-green-500/50"
                      } animate-pulse`}
                    >
                      {entry.slots_filled} / {OFFICE_CAPACITY} Slots Filled
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div>
                    <h6 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                      <Zap className="w-4 h-4 text-yellow-400" />
                      Who's coming:
                    </h6>
                    {entry.attendees.length > 0 ? (
                      <ul className="space-y-1">
                        {entry.attendees.map((name, idx) => (
                          <li
                            key={idx}
                            className="text-gray-400 text-sm flex items-center gap-2 p-2 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-cyan-400/50 transition-all duration-300"
                          >
                            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                            {name}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-500 italic">No one yet.</p>
                    )}
                  </div>

                  <div className="border-t border-slate-700/50 pt-4">
                    {!entry.is_past ? (
                      <div className="space-y-3">
                        {entry.user_choice?.status === "Yes" ? (
                          <div className="text-center space-y-3">
                            <div className="flex items-center justify-center gap-2 text-green-400 font-semibold">
                              <Check className="w-5 h-5" />
                              You are attending
                            </div>
                            {entry.user_choice.was_auto_assigned && (
                              <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">Auto-Assigned</Badge>
                            )}
                            <div className="space-y-2">
                              <InteractiveButton
                                variant="outline"
                                className="w-full border-purple-500/50 text-purple-400 hover:bg-purple-500/20"
                                onClick={() => {
                                  /* Handle swap request */
                                }}
                              >
                                <Shuffle className="w-4 h-4 mr-2" />
                                Request Swap
                              </InteractiveButton>
                              {!entry.user_choice.was_auto_assigned && (
                                <InteractiveButton
                                  variant="outline"
                                  className="w-full border-red-500/50 text-red-400 hover:bg-red-500/20"
                                  onClick={() => handleAttendanceChange(entry.id, "No")}
                                  disabled={isLoading}
                                >
                                  <X className="w-4 h-4 mr-2" />
                                  Cancel Attendance
                                </InteractiveButton>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {entry.slots_filled < OFFICE_CAPACITY && (
                              <div className="space-y-2">
                                <Select value={selectedMeal} onValueChange={setSelectedMeal}>
                                  <SelectTrigger className="w-full bg-slate-800/50 border-slate-600/50 text-white">
                                    <SelectValue placeholder="Select meal preference" />
                                  </SelectTrigger>
                                  <SelectContent className="bg-slate-800 border-slate-600">
                                    <SelectItem value="vegetarian">Vegetarian</SelectItem>
                                    <SelectItem value="non-vegetarian">Non-Vegetarian</SelectItem>
                                    <SelectItem value="vegan">Vegan</SelectItem>
                                  </SelectContent>
                                </Select>

                                <InteractiveButton
                                  className="w-full bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600"
                                  onClick={() => handleAttendanceChange(entry.id, "Yes", selectedMeal)}
                                  disabled={isLoading}
                                >
                                  <ArrowRight className="w-4 h-4 mr-2" />
                                  I'm Coming
                                </InteractiveButton>
                              </div>
                            )}

                            <InteractiveButton
                              variant="outline"
                              className="w-full border-gray-500/50 text-gray-400 hover:bg-gray-500/20"
                              onClick={() => handleAttendanceChange(entry.id, "No")}
                              disabled={isLoading}
                            >
                              I'm Not Coming
                            </InteractiveButton>

                            <div className="pt-2">
                              <InteractiveButton
                                variant="outline"
                                size="sm"
                                className={`w-full ${
                                  entry.user_choice?.is_available
                                    ? "border-red-500/50 text-red-400 hover:bg-red-500/20"
                                    : "border-green-500/50 text-green-400 hover:bg-green-500/20"
                                }`}
                                onClick={() => toggleAvailability(entry.id)}
                                disabled={isLoading}
                              >
                                {entry.user_choice?.is_available
                                  ? "I'm Not Available for Swaps"
                                  : "Make me Available for Swaps"}
                              </InteractiveButton>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-center text-gray-500 italic">This day is in the past.</p>
                    )}
                  </div>
                </CardContent>
              </GlowingCard>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Menu, X, Home, LogOut, Shield, User } from "lucide-react"

export default function FuturisticNavbar() {
  const [isOpen, setIsOpen] = useState(false)
  const currentUser = { username: "John Doe", is_admin: true, is_anonymous: false }

  return (
    <nav className="relative z-20 bg-black/20 backdrop-blur-xl border-b border-cyan-500/20">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <span className="text-white font-bold text-xl bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              Arcwide Office Planner
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            {!currentUser.is_anonymous ? (
              <>
                <span className="text-cyan-400 font-medium">Hello, {currentUser.username}!</span>
                {currentUser.is_admin && (
                  <Button variant="ghost" className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/20">
                    <Shield className="w-4 h-4 mr-2" />
                    Admin
                  </Button>
                )}
                <Button variant="ghost" className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/20">
                  <Home className="w-4 h-4 mr-2" />
                  Home
                </Button>
                <Button variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-500/20">
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <Button variant="ghost" className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/20">
                <User className="w-4 h-4 mr-2" />
                Login
              </Button>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(!isOpen)}
              className="text-cyan-400 hover:text-cyan-300"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden py-4 space-y-2 border-t border-cyan-500/20">
            {!currentUser.is_anonymous ? (
              <>
                <div className="text-cyan-400 font-medium px-4 py-2">Hello, {currentUser.username}!</div>
                {currentUser.is_admin && (
                  <Button
                    variant="ghost"
                    className="w-full justify-start text-purple-400 hover:text-purple-300 hover:bg-purple-500/20"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Admin
                  </Button>
                )}
                <Button
                  variant="ghost"
                  className="w-full justify-start text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/20"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Home
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start text-red-400 hover:text-red-300 hover:bg-red-500/20"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <Button
                variant="ghost"
                className="w-full justify-start text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/20"
              >
                <User className="w-4 h-4 mr-2" />
                Login
              </Button>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}

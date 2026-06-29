/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from 'react'
import { User } from '../types'
import { ClutchApi } from '../api'

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('clutch_token'))
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (token) {
      ClutchApi.me()
        .then((u) => {
          setUser(u)
        })
        .catch(() => {
          setToken(null)
          setUser(null)
          localStorage.removeItem('clutch_token')
        })
        .finally(() => setIsLoading(false))
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsLoading(false)
    }
  }, [token])

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('clutch_token', newToken)
    setToken(newToken)
    setUser(newUser)
  }

  const logout = () => {
    localStorage.removeItem('clutch_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

import React from 'react'
import { Route, Routes, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import WarRoom from './pages/WarRoom'
import Crisis from './pages/Crisis'
import Toolkit from './pages/Toolkit'
import Auth from './pages/Auth'
import { useAuth } from './lib/auth'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center text-white/40">Loading...</div>
  if (!user) return <Navigate to="/auth" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<Auth />} />
      <Route path="/war-room" element={<RequireAuth><WarRoom /></RequireAuth>} />
      <Route path="/toolkit" element={<RequireAuth><Toolkit /></RequireAuth>} />
      <Route path="/crisis" element={<RequireAuth><Crisis /></RequireAuth>} />
      <Route path="*" element={<Landing />} />
    </Routes>
  )
}

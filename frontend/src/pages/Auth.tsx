import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { ClutchApi } from '../api'

export default function Auth() {
  const { login, user } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const extractError = (err: any): string => {
    // FastAPI 422 returns detail as an array of validation objects in the response body
    const raw = err?.body?.detail ?? err?.detail
    if (Array.isArray(raw)) return raw.map((e: any) => e.msg ?? JSON.stringify(e)).join('; ')
    if (typeof raw === 'string' && raw !== '[object Object]') return raw
    return err?.message || 'An error occurred'
  }
  const [loading, setLoading] = useState(false)

  if (user) {
    return <Navigate to="/war-room" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (isLogin) {
        const res = await ClutchApi.login({ email, password })
        login(res.access_token, res.user)
      } else {
        const res = await ClutchApi.register({ email, password, display_name: displayName })
        login(res.access_token, res.user)
      }
    } catch (err: any) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = async () => {
    setError(null)
    setLoading(true)
    try {
      const res = await ClutchApi.demoLogin()
      login(res.access_token, res.user)
    } catch (err: any) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#131314] rounded-2xl border border-white/5 p-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-white mb-2">Clutch</h1>
        <p className="text-white/60 mb-8">{isLogin ? 'Welcome back.' : 'Create an account.'}</p>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                className="w-full bg-[#1C1D1F] border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#4B8BFF] transition-colors"
                placeholder="How should we call you?"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-[#1C1D1F] border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#4B8BFF] transition-colors"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-white/60 mb-1.5 uppercase tracking-wider">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full bg-[#1C1D1F] border border-white/10 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-[#4B8BFF] transition-colors"
              placeholder="min. 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#4B8BFF] hover:bg-[#3B7BFF] text-white font-medium rounded-lg px-4 py-2.5 transition-colors mt-6 disabled:opacity-50"
          >
            {loading ? 'Processing...' : isLogin ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/5 space-y-4">
          <button
            onClick={handleDemo}
            disabled={loading}
            className="w-full bg-white/5 hover:bg-white/10 text-white font-medium rounded-lg px-4 py-2.5 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            Use Demo Account
          </button>
          
          <button
            onClick={() => { setIsLogin(!isLogin); setError(null) }}
            className="w-full text-sm text-white/40 hover:text-white/80 transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </button>
        </div>
      </div>
    </div>
  )
}

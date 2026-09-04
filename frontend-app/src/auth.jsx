import { createContext, useContext, useMemo, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { api } from './api'

const AuthContext = createContext(null)

function readUser() {
  const id = localStorage.getItem('user_id')
  const nome = localStorage.getItem('username')
  if (!localStorage.getItem('access_token') || !nome) return null
  return { id, nome }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)

  function persistSession(data) {
    localStorage.setItem('access_token', data.access_token)
    if (data.user?.nome) localStorage.setItem('username', data.user.nome)
    if (data.user?.id) localStorage.setItem('user_id', String(data.user.id))
    setUser(readUser())
  }

  async function login(nome, password) {
    const data = await api.login(nome, password)
    persistSession(data)
    return data
  }

  async function register(nome, password) {
    await api.register(nome, password)
    return login(nome, password)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    localStorage.removeItem('obra_id')
    localStorage.removeItem('obra_papel')
    localStorage.removeItem('obra_nome')
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user && localStorage.getItem('access_token')),
      login,
      register,
      logout,
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}

export function RequireAuth() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/" replace state={{ from: location }} />
  }
  return <Outlet />
}

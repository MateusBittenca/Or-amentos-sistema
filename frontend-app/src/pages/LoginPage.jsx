import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Button, Card, Field, inputClass } from '../components/ui'

export default function LoginPage() {
  const { isAuthenticated, login, register } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    const pending = localStorage.getItem('pending_invite_token')
    return <Navigate to={pending ? `/convite/${pending}` : '/obras'} replace />
  }

  async function afterAuth() {
    const pending = localStorage.getItem('pending_invite_token')
    navigate(pending ? `/convite/${pending}` : '/obras', { replace: true })
  }

  async function handleLogin(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      await afterAuth()
    } catch (err) {
      setError(err.message || 'Usuário ou senha inválidos')
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setError('')
    if (password.length < 4) {
      setError('A senha precisa ter no mínimo 4 caracteres')
      return
    }
    setLoading(true)
    try {
      await register(email.trim(), password)
      await afterAuth()
    } catch (err) {
      setError(err.message || 'Erro ao criar conta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-blue-800 text-white shadow-md">
        <div className="container mx-auto px-4 py-3">
          <h1 className="font-bold flex items-center">
            <i className="fas fa-hard-hat mr-2" />Gestão de Gastos
          </h1>
        </div>
      </nav>
      <div className="flex-grow flex items-center justify-center px-4 py-10">
        <Card className="w-full max-w-md overflow-hidden">
          <div className="p-8">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
                <i className="fas fa-hard-hat text-blue-600 text-3xl" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Bem-vindo(a)</h2>
              <p className="text-gray-600 text-sm mt-1">Acesse sua conta para continuar</p>
            </div>

            <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
              <button
                type="button"
                className={`flex-1 py-2 rounded-lg text-sm font-medium ${tab === 'login' ? 'bg-white shadow text-blue-800' : 'text-gray-600'}`}
                onClick={() => { setTab('login'); setError('') }}
              >
                Entrar
              </button>
              <button
                type="button"
                className={`flex-1 py-2 rounded-lg text-sm font-medium ${tab === 'register' ? 'bg-white shadow text-blue-800' : 'text-gray-600'}`}
                onClick={() => { setTab('register'); setError('') }}
              >
                Criar conta
              </button>
            </div>

            {error ? <p className="mb-3 text-sm text-red-600 bg-red-50 rounded-lg p-2">{error}</p> : null}

            <form onSubmit={tab === 'login' ? handleLogin : handleRegister}>
              <Field label="E-mail">
                <input className={inputClass()} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </Field>
              <Field label="Senha">
                <div className="relative">
                  <input
                    className={`${inputClass()} pr-10`}
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button type="button" className="absolute right-3 top-2.5 text-gray-400" onClick={() => setShowPassword(!showPassword)}>
                    <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`} />
                  </button>
                </div>
              </Field>
              <Button type="submit" loading={loading} className="w-full">
                {tab === 'login' ? 'Acessar sistema' : 'Criar conta'}
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  )
}

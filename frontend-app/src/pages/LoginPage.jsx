import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Button, Card, Field, inputClass } from '../components/ui'
import { useToast } from '../components/Toast'

export default function LoginPage() {
  const { isAuthenticated, login, register } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [forgot, setForgot] = useState(false)
  const [resetUser, setResetUser] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [resetStep, setResetStep] = useState('request')
  const [resetMessage, setResetMessage] = useState('')

  if (isAuthenticated && !forgot) {
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

  async function handleResetRequest(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await api.requestPasswordReset(resetUser.trim())
      setResetMessage(data.message)
      setResetStep('confirm')
    } catch (err) {
      setError(err.message || 'Erro ao solicitar redefinição')
    } finally {
      setLoading(false)
    }
  }

  async function handleResetConfirm(e) {
    e.preventDefault()
    setError('')
    if (newPassword !== confirmPassword) {
      setError('As senhas não coincidem')
      return
    }
    setLoading(true)
    try {
      await api.resetPassword(resetUser.trim(), resetToken, newPassword)
      showToast('Senha redefinida. Entre com a nova senha.')
      setForgot(false)
      setResetStep('request')
      setEmail(resetUser)
    } catch (err) {
      setError(err.message || 'Erro ao redefinir senha')
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
              <h2 className="text-2xl font-bold text-gray-800">
                {forgot ? 'Recuperar senha' : 'Bem-vindo(a)'}
              </h2>
              <p className="text-gray-600 text-sm mt-1">
                {forgot ? 'Redefina o acesso à sua conta' : 'Acesse sua conta para continuar'}
              </p>
            </div>

            {!forgot && (
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
            )}

            {error ? <p className="mb-3 text-sm text-red-600 bg-red-50 rounded-lg p-2">{error}</p> : null}

            {forgot ? (
              resetStep === 'request' ? (
                <form onSubmit={handleResetRequest}>
                  <Field label="E-mail">
                    <input className={inputClass()} type="email" value={resetUser} onChange={(e) => setResetUser(e.target.value)} required />
                  </Field>
                  <Button type="submit" loading={loading} className="w-full">Enviar solicitação</Button>
                  <button type="button" className="mt-4 text-sm text-blue-600" onClick={() => setForgot(false)}>Voltar ao login</button>
                </form>
              ) : (
                <form onSubmit={handleResetConfirm}>
                  {resetMessage ? <p className="mb-3 text-sm text-green-700 bg-green-50 rounded-lg p-2">{resetMessage}</p> : null}
                  <Field label="Token de recuperação">
                    <input className={inputClass()} value={resetToken} onChange={(e) => setResetToken(e.target.value)} required />
                  </Field>
                  <Field label="Nova senha">
                    <input className={inputClass()} type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
                  </Field>
                  <Field label="Confirmar senha">
                    <input className={inputClass()} type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
                  </Field>
                  <Button type="submit" loading={loading} className="w-full">Redefinir senha</Button>
                </form>
              )
            ) : (
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
                {tab === 'login' ? (
                  <button type="button" className="text-sm text-blue-600 mb-4" onClick={() => { setForgot(true); setError('') }}>
                    Esqueceu a senha?
                  </button>
                ) : null}
                <Button type="submit" loading={loading} className="w-full">
                  {tab === 'login' ? 'Acessar sistema' : 'Criar conta'}
                </Button>
              </form>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

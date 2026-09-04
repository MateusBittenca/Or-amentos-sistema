import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Button, Card } from '../components/ui'
import { useToast } from '../components/Toast'

export default function ConvitePage() {
  const { token } = useParams()
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [invite, setInvite] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [accepting, setAccepting] = useState(false)

  useEffect(() => {
    if (token) localStorage.setItem('pending_invite_token', token)
    async function load() {
      try {
        const data = await api.getPublic(`/convite/${encodeURIComponent(token)}`)
        setInvite(data)
      } catch (err) {
        setError(err.message || 'Convite inválido')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token])

  async function accept() {
    if (!isAuthenticated) {
      navigate('/', { replace: true })
      return
    }
    setAccepting(true)
    try {
      const data = await api.postJson(`/convite/${encodeURIComponent(token)}/aceitar`, {})
      localStorage.removeItem('pending_invite_token')
      localStorage.setItem('obra_id', String(data.obra_id))
      localStorage.setItem('obra_papel', data.papel)
      showToast('Convite aceito')
      navigate(`/obras/${data.obra_id}`, { replace: true })
    } catch (err) {
      setError(err.message || 'Não foi possível aceitar o convite')
    } finally {
      setAccepting(false)
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
        <Card className="w-full max-w-md p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
            <i className="fas fa-envelope-open-text text-blue-600 text-3xl" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Convite para obra</h2>
          {loading ? <p className="text-gray-600">Carregando convite...</p> : null}
          {invite ? (
            <p className="text-gray-600 mb-6">
              Você foi convidado para <strong>{invite.obra_nome}</strong> como {invite.papel}.
            </p>
          ) : null}
          {error ? <p className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</p> : null}
          {invite && !error ? (
            <Button className="w-full" loading={accepting} onClick={accept}>
              {isAuthenticated ? 'Aceitar convite' : 'Entrar para aceitar'}
            </Button>
          ) : null}
          <p className="mt-4 text-sm">
            <Link className="text-blue-600" to={isAuthenticated ? '/obras' : '/'}>Voltar</Link>
          </p>
        </Card>
      </div>
    </div>
  )
}

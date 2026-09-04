import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Button, Card, EmptyState, Field, Modal, inputClass } from '../components/ui'
import { useToast } from '../components/Toast'

export default function ObrasPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [obras, setObras] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [nome, setNome] = useState('')
  const [descricao, setDescricao] = useState('')
  const [saving, setSaving] = useState(false)
  const pending = localStorage.getItem('pending_invite_token')

  async function load() {
    setError('')
    try {
      const data = await api.get('/obras')
      setObras(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message || 'Erro ao carregar obras')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function enterObra(obra) {
    localStorage.setItem('obra_id', String(obra.id))
    localStorage.setItem('obra_papel', obra.papel)
    localStorage.setItem('obra_nome', obra.nome)
    navigate(`/obras/${obra.id}`)
  }

  async function createObra(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const obra = await api.postJson('/obras', { nome: nome.trim(), descricao: descricao.trim() || null })
      showToast('Obra criada')
      enterObra(obra)
    } catch (err) {
      showToast(err.message || 'Erro ao criar obra', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-blue-800 text-white shadow-md">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between gap-3 flex-wrap">
          <h1 className="font-bold flex items-center">
            <i className="fas fa-hard-hat mr-2" />Gestão de Gastos
          </h1>
          <div className="flex items-center gap-3 text-sm">
            <span className="bg-white bg-opacity-10 rounded-full px-3 py-1">
              <i className="fas fa-user-circle mr-2" />{user?.nome}
            </span>
            <button type="button" className="hover:underline" onClick={logout}>Sair</button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 flex-grow">
        {pending ? (
          <div className="mb-6 bg-blue-50 text-blue-800 rounded-xl p-4 flex items-center justify-between gap-3">
            <p>Você tem um convite pendente.</p>
            <Link to={`/convite/${pending}`} className="font-medium underline">Ver convite</Link>
          </div>
        ) : null}

        <div className="flex items-center justify-between mb-6 gap-3 flex-wrap">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Minhas obras</h2>
            <p className="text-sm text-gray-600 mt-1">Entre em uma obra ou crie uma nova.</p>
          </div>
          <Button onClick={() => setOpen(true)}>
            <i className="fas fa-plus mr-2" />Nova obra
          </Button>
        </div>

        {error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null}

        {loading ? (
          <p className="text-gray-500">Carregando obras...</p>
        ) : obras.length === 0 ? (
          <Card className="p-8">
            <EmptyState title="Crie a primeira obra" text="Você ainda não participa de nenhuma obra." />
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {obras.map((obra) => (
              <Card key={obra.id} className="p-5">
                <h3 className="text-lg font-bold text-gray-800 mb-1">{obra.nome}</h3>
                <p className="text-sm text-gray-500 mb-3">{obra.descricao || 'Sem descrição'}</p>
                <span className="inline-block text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full mb-4">{obra.papel}</span>
                <Button className="w-full" onClick={() => enterObra(obra)}>Entrar</Button>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Modal
        open={open}
        title="Nova obra"
        onClose={() => setOpen(false)}
        footer={(
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>Cancelar</Button>
            <Button type="submit" form="createObraForm" loading={saving}>Criar obra</Button>
          </>
        )}
      >
        <form id="createObraForm" onSubmit={createObra}>
          <Field label="Nome">
            <input className={inputClass()} value={nome} onChange={(e) => setNome(e.target.value)} required />
          </Field>
          <Field label="Descrição (opcional)">
            <input className={inputClass()} value={descricao} onChange={(e) => setDescricao(e.target.value)} />
          </Field>
        </form>
      </Modal>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { useOutletContext, useParams } from 'react-router-dom'
import { api } from '../api'
import { canEditObra, canPayObra, isPaid, paidTotal, activityValue } from '../constants'
import { formatCurrency } from '../format'
import { Button, Card, EmptyState, StatusPill } from '../components/ui'
import { useToast } from '../components/Toast'
import ActivityFormModal from '../components/ActivityFormModal'
import PaymentModal from '../components/PaymentModal'

const TABS = [
  { id: 'all', label: 'Todas' },
  { id: 'pending', label: 'Pendentes' },
  { id: 'paid', label: 'Pagas' },
]

export default function AtividadesPage() {
  const { obraId } = useParams()
  const { obra } = useOutletContext()
  const { showToast } = useToast()
  const [tab, setTab] = useState('all')
  const [query, setQuery] = useState('')
  const [activities, setActivities] = useState([])
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [payActivity, setPayActivity] = useState(null)
  const papel = obra?.papel || localStorage.getItem('obra_papel')

  async function load() {
    setError('')
    try {
      const data = await api.get('/atividades', obraId)
      setActivities(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message || 'Erro ao carregar atividades')
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => { load() }, [obraId])

  const filtered = useMemo(() => {
    return activities.filter((activity) => {
      const paid = isPaid(activity)
      if (tab === 'pending' && paid) return false
      if (tab === 'paid' && !paid) return false
      if (!query.trim()) return true
      const hay = `${activity.activity} ${activity.sector}`.toLowerCase()
      return hay.includes(query.toLowerCase())
    })
  }, [activities, tab, query])

  async function removeActivity(activity) {
    if (!window.confirm(`Excluir "${activity.activity}"?`)) return
    try {
      await api.del(`/delete-activity/${activity.id}`, obraId)
      showToast('Atividade excluída')
      load()
    } catch (err) {
      showToast(err.message || 'Erro ao excluir', 'error')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <h2 className="text-xl font-semibold text-blue-800">Atividades</h2>
        {canEditObra(papel) ? (
          <Button onClick={() => setAddOpen(true)}>
            <i className="fas fa-plus mr-2" />Adicionar atividade
          </Button>
        ) : null}
      </div>

      <Card className="p-4">
        <div className="flex flex-wrap gap-2 border-b mb-4">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`px-4 py-2 text-sm font-medium ${tab === item.id ? 'text-blue-700 border-b-2 border-blue-600' : 'text-gray-500'}`}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2 mb-4">
          <input
            className="input-focus w-full px-3 py-2 border rounded-lg"
            placeholder="Buscar atividade..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {error ? <p className="text-sm text-red-600 mb-3">{error}</p> : null}
        {!loaded ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : filtered.length === 0 ? (
          <EmptyState text="Nenhuma atividade encontrada" />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100 text-gray-600">
                <tr>
                  <th className="text-left py-2 px-3">Setor</th>
                  <th className="text-left py-2 px-3">Atividade</th>
                  <th className="text-left py-2 px-3">Valor</th>
                  <th className="text-left py-2 px-3">Pago</th>
                  <th className="text-left py-2 px-3">Data</th>
                  <th className="text-left py-2 px-3">Status</th>
                  <th className="text-left py-2 px-3">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((activity) => (
                  <tr key={activity.id} className="border-t hover:bg-gray-50">
                    <td className="py-2 px-3">{activity.sector}</td>
                    <td className="py-2 px-3">{activity.activity}</td>
                    <td className="py-2 px-3">{formatCurrency(activityValue(activity))}</td>
                    <td className="py-2 px-3">{formatCurrency(paidTotal(activity))}</td>
                    <td className="py-2 px-3">{activity.date || '-'}</td>
                    <td className="py-2 px-3"><StatusPill paid={isPaid(activity)} /></td>
                    <td className="py-2 px-3 space-x-2 whitespace-nowrap">
                      {(canPayObra(papel) || isPaid(activity)) ? (
                        <button type="button" className="bg-blue-50 text-blue-800 px-3 py-1 rounded-lg" onClick={() => setPayActivity(activity)}>
                          {isPaid(activity) ? 'Comprovante' : 'Pagar'}
                        </button>
                      ) : null}
                      {canEditObra(papel) ? (
                        <button type="button" className="text-red-600" onClick={() => removeActivity(activity)}>Excluir</button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <ActivityFormModal
        open={addOpen}
        obraId={obraId}
        onClose={() => setAddOpen(false)}
        onSaved={() => { setAddOpen(false); showToast('Atividade adicionada'); load() }}
      />
      <PaymentModal
        activity={payActivity}
        obraId={obraId}
        papel={papel}
        onClose={() => setPayActivity(null)}
        onSaved={() => { setPayActivity(null); showToast('Pagamento registrado'); load() }}
      />
    </div>
  )
}

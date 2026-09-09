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

  function activityActions(activity, stacked) {
    return (
      <div className={stacked ? 'flex gap-2' : 'flex items-center justify-end gap-2 whitespace-nowrap'}>
        {(canPayObra(papel) || isPaid(activity)) ? (
          <button
            type="button"
            className={`bg-blue-50 text-blue-800 px-3 py-1.5 rounded-lg text-sm font-medium ${stacked ? 'flex-1' : ''}`}
            onClick={() => setPayActivity(activity)}
          >
            {isPaid(activity) ? 'Comprovante' : 'Pagar'}
          </button>
        ) : null}
        {canEditObra(papel) ? (
          <button
            type="button"
            className={`text-red-600 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-red-50 ${stacked ? 'flex-1' : ''}`}
            onClick={() => removeActivity(activity)}
          >
            Excluir
          </button>
        ) : null}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <h2 className="text-xl font-semibold text-blue-800">Atividades</h2>
        {canEditObra(papel) ? (
          <Button className="w-full sm:w-auto" onClick={() => setAddOpen(true)}>
            <i className="fas fa-plus mr-2" />Adicionar atividade
          </Button>
        ) : null}
      </div>

      <Card className="overflow-hidden">
        <div className="p-4 pb-0">
          <div className="flex flex-wrap gap-2 border-b">
            {TABS.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`px-3 sm:px-4 py-2 text-sm font-medium ${tab === item.id ? 'text-blue-700 border-b-2 border-blue-600' : 'text-gray-500'}`}
                onClick={() => setTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="py-4">
            <input
              className="input-focus w-full px-3 py-2 border rounded-lg"
              placeholder="Buscar atividade..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          {error ? <p className="text-sm text-red-600 pb-3">{error}</p> : null}
        </div>
        {!loaded ? (
          <p className="text-sm text-gray-500 px-4 pb-4">Carregando...</p>
        ) : filtered.length === 0 ? (
          <div className="px-4 pb-4">
            <EmptyState text="Nenhuma atividade encontrada" />
          </div>
        ) : (
          <>
            <div className="lg:hidden divide-y divide-gray-100">
              {filtered.map((activity) => (
                <div key={activity.id} className="px-4 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium text-gray-800 leading-snug">{activity.activity}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {activity.sector || 'Sem setor'}
                        {activity.date ? ` · ${activity.date}` : ''}
                      </p>
                    </div>
                    <StatusPill paid={isPaid(activity)} />
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-gray-500">Valor</p>
                      <p className="font-semibold text-gray-800 tabular-nums">{formatCurrency(activityValue(activity))}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Pago</p>
                      <p className="font-semibold text-gray-800 tabular-nums">{formatCurrency(paidTotal(activity))}</p>
                    </div>
                  </div>
                  <div className="mt-3">{activityActions(activity, true)}</div>
                </div>
              ))}
            </div>
            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                  <tr>
                    <th className="text-left font-medium py-3 px-4">Setor</th>
                    <th className="text-left font-medium py-3 px-4">Atividade</th>
                    <th className="text-right font-medium py-3 px-4">Valor</th>
                    <th className="text-right font-medium py-3 px-4">Pago</th>
                    <th className="text-left font-medium py-3 px-4">Data</th>
                    <th className="text-left font-medium py-3 px-4">Status</th>
                    <th className="text-right font-medium py-3 px-4">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filtered.map((activity) => (
                    <tr key={activity.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 text-gray-600 whitespace-nowrap">{activity.sector || '-'}</td>
                      <td className="py-3 px-4 font-medium text-gray-800 max-w-xs truncate">{activity.activity}</td>
                      <td className="py-3 px-4 text-right tabular-nums whitespace-nowrap">{formatCurrency(activityValue(activity))}</td>
                      <td className="py-3 px-4 text-right tabular-nums whitespace-nowrap">{formatCurrency(paidTotal(activity))}</td>
                      <td className="py-3 px-4 text-gray-600 whitespace-nowrap">{activity.date || '-'}</td>
                      <td className="py-3 px-4"><StatusPill paid={isPaid(activity)} /></td>
                      <td className="py-3 px-4">{activityActions(activity, false)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
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

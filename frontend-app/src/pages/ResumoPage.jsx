import { useEffect, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import { api } from '../api'
import { canEditObra, paidTotal, isPaid } from '../constants'
import { formatCurrency } from '../format'
import { Button, Card, EmptyState, Kpi, StatusPill } from '../components/ui'
import { useToast } from '../components/Toast'
import ActivityFormModal from '../components/ActivityFormModal'
import PaymentModal from '../components/PaymentModal'

export default function ResumoPage() {
  const { obraId } = useParams()
  const { obra } = useOutletContext()
  const { showToast } = useToast()
  const [total, setTotal] = useState(0)
  const [pago, setPago] = useState(0)
  const [membros, setMembros] = useState([])
  const [activities, setActivities] = useState([])
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [payActivity, setPayActivity] = useState(null)

  async function load() {
    setError('')
    try {
      const [totalData, pagoData, membrosData, atividades] = await Promise.all([
        api.get('/valor-total', obraId),
        api.get('/valor-total-pago', obraId),
        api.get('/valor-pago-membros', obraId),
        api.get('/atividades', obraId),
      ])
      setTotal(Number(totalData.total || 0))
      setPago(Number(pagoData.total_pago || 0))
      setMembros(Array.isArray(membrosData) ? membrosData : [])
      setActivities(Array.isArray(atividades) ? atividades : [])
    } catch (err) {
      setError(err.message || 'Erro ao carregar resumo')
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => { load() }, [obraId])

  const restante = total - pago
  const pct = total > 0 ? ((pago / total) * 100).toFixed(0) : '0'
  const recent = activities.slice(0, 8)
  const hasPayments = membros.some((item) => Number(item.total) > 0)
  const canEdit = canEditObra(obra?.papel || localStorage.getItem('obra_papel'))

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <h2 className="text-xl font-semibold text-blue-800">Resumo</h2>
        {canEdit ? (
          <Button onClick={() => setAddOpen(true)}>
            <i className="fas fa-plus mr-2" />Adicionar atividade
          </Button>
        ) : null}
      </div>

      {error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <Kpi label="Valor total da obra" value={formatCurrency(total)} icon="fa-coins" />
        <Kpi label="Valor pago" value={formatCurrency(pago)} icon="fa-check-circle" />
        <Kpi label="Restante" value={formatCurrency(restante)} hint={`${pct}% pago`} icon="fa-hourglass-half" />
      </div>

      <Card className="p-4 mb-4">
        <h3 className="text-lg font-semibold text-blue-800 mb-3">
          <i className="fas fa-users mr-2" />Pago por membro
        </h3>
        {!loaded ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : !hasPayments ? (
          <EmptyState icon="fa-wallet" text="Nenhum pagamento ainda" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {membros.map((item) => (
              <div key={item.usuario_id} className="flex items-center justify-between bg-blue-50 rounded-lg px-3 py-2">
                <span className="text-sm text-gray-700 truncate">{item.nome}</span>
                <span className="font-bold text-gray-800 ml-2">{formatCurrency(item.total)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-blue-800">Atividades recentes</h3>
          <Link to={`/obras/${obraId}/atividades`} className="text-sm text-blue-700">Ver todas</Link>
        </div>
        {!loaded ? null : recent.length === 0 ? (
          <EmptyState text="Nenhuma atividade nesta obra" />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100 text-gray-600">
                <tr>
                  <th className="text-left py-2 px-3">Atividade</th>
                  <th className="text-left py-2 px-3">Valor</th>
                  <th className="text-left py-2 px-3">Status</th>
                  <th className="text-left py-2 px-3" />
                </tr>
              </thead>
              <tbody>
                {recent.map((activity) => (
                  <tr key={activity.id} className="border-t">
                    <td className="py-2 px-3">{activity.activity}</td>
                    <td className="py-2 px-3">{formatCurrency(activity.value)}</td>
                    <td className="py-2 px-3"><StatusPill paid={isPaid(activity)} /></td>
                    <td className="py-2 px-3">
                      <button type="button" className="text-blue-700 text-sm" onClick={() => setPayActivity(activity)}>
                        {isPaid(activity) ? 'Comprovante' : 'Pagar'}
                      </button>
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
        papel={obra?.papel}
        onClose={() => setPayActivity(null)}
        onSaved={() => { setPayActivity(null); showToast('Pagamento registrado'); load() }}
      />
    </div>
  )
}

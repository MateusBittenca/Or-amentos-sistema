import { useEffect, useState } from 'react'
import { Link, useOutletContext, useParams } from 'react-router-dom'
import { api } from '../api'
import { canEditObra, isPaid } from '../constants'
import { formatCurrency } from '../format'
import { Button, Card, EmptyState, Kpi, StatusPill } from '../components/ui'
import { useToast } from '../components/Toast'
import ActivityFormModal from '../components/ActivityFormModal'
import PaymentModal from '../components/PaymentModal'

function saldoLabel(saldo) {
  const value = Number(saldo || 0)
  if (value > 0.009) return { text: `Deve ${formatCurrency(value)}`, className: 'text-amber-800 bg-amber-50' }
  if (value < -0.009) return { text: `A receber ${formatCurrency(-value)}`, className: 'text-green-800 bg-green-50' }
  return { text: 'Em dia', className: 'text-gray-600 bg-gray-100' }
}

export default function ResumoPage() {
  const { obraId } = useParams()
  const { obra } = useOutletContext()
  const { showToast } = useToast()
  const [total, setTotal] = useState(0)
  const [pago, setPago] = useState(0)
  const [restante, setRestante] = useState(0)
  const [saldos, setSaldos] = useState([])
  const [transferencias, setTransferencias] = useState([])
  const [activities, setActivities] = useState([])
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [payActivity, setPayActivity] = useState(null)

  async function load() {
    setError('')
    try {
      const data = await api.get(`/obras/${obraId}/resumo`)
      setTotal(Number(data.total || 0))
      setPago(Number(data.total_pago || 0))
      setRestante(Number(data.restante || 0))
      setSaldos(Array.isArray(data.saldos) ? data.saldos : [])
      setTransferencias(Array.isArray(data.transferencias) ? data.transferencias : [])
      setActivities(Array.isArray(data.atividades) ? data.atividades : [])
    } catch (err) {
      setError(err.message || 'Erro ao carregar resumo')
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => { load() }, [obraId])

  const pct = total > 0 ? ((pago / total) * 100).toFixed(0) : '0'
  const recent = activities.slice(0, 8)
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
          <i className="fas fa-balance-scale mr-2" />Quem deve quanto
        </h3>
        <p className="text-xs text-gray-500 mb-3">A divisão é só do que já foi pago, pela participação de cada atividade.</p>
        {!loaded ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : saldos.length === 0 ? (
          <EmptyState icon="fa-wallet" text="Nenhum membro nesta obra" />
        ) : (
          <>
            {transferencias.length === 0 ? (
              <p className="text-sm text-green-800 bg-green-50 rounded-lg px-3 py-2 mb-3">
                Ninguém deve nada pelo que já foi gasto.
              </p>
            ) : (
              <ul className="mb-3 space-y-2">
                {transferencias.map((item) => (
                  <li
                    key={`${item.de_usuario_id}-${item.para_usuario_id}`}
                    className="text-sm font-medium text-blue-900 bg-blue-50 rounded-lg px-3 py-2"
                  >
                    {item.de_nome} transfere {formatCurrency(item.valor)} para {item.para_nome}
                  </li>
                ))}
              </ul>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {saldos.map((item) => {
                const badge = saldoLabel(item.saldo)
                return (
                  <div key={item.usuario_id} className="rounded-lg border border-gray-100 px-3 py-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-gray-800 truncate">{item.nome}</span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${badge.className}`}>{badge.text}</span>
                    </div>
                    <div className="mt-2 flex justify-between text-xs text-gray-500">
                      <span>Pago {formatCurrency(item.pago)}</span>
                      <span>Parte {formatCurrency(item.parte)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </Card>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between gap-3 px-4 py-4">
          <h3 className="text-lg font-semibold text-blue-800">Atividades recentes</h3>
          <Link to={`/obras/${obraId}/atividades`} className="text-sm text-blue-700 shrink-0">Ver todas</Link>
        </div>
        {!loaded ? null : recent.length === 0 ? (
          <div className="px-4 pb-4">
            <EmptyState text="Nenhuma atividade nesta obra" />
          </div>
        ) : (
          <>
            <div className="md:hidden divide-y divide-gray-100">
              {recent.map((activity) => (
                <div key={activity.id} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium text-gray-800 leading-snug min-w-0">{activity.activity}</p>
                    <StatusPill activity={activity} />
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold tabular-nums text-gray-800">{formatCurrency(activity.value)}</p>
                    <button type="button" className="text-blue-700 text-sm font-medium" onClick={() => setPayActivity(activity)}>
                      {isPaid(activity) ? 'Comprovante' : 'Pagar'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                  <tr>
                    <th className="text-left font-medium py-3 px-4">Atividade</th>
                    <th className="text-right font-medium py-3 px-4">Valor</th>
                    <th className="text-left font-medium py-3 px-4">Status</th>
                    <th className="text-right font-medium py-3 px-4">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {recent.map((activity) => (
                    <tr key={activity.id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-800 max-w-xs truncate">{activity.activity}</td>
                      <td className="py-3 px-4 text-right tabular-nums whitespace-nowrap">{formatCurrency(activity.value)}</td>
                      <td className="py-3 px-4"><StatusPill activity={activity} /></td>
                      <td className="py-3 px-4 text-right">
                        <button type="button" className="text-blue-700 text-sm font-medium" onClick={() => setPayActivity(activity)}>
                          {isPaid(activity) ? 'Comprovante' : 'Pagar'}
                        </button>
                      </td>
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
        papel={obra?.papel}
        onClose={() => setPayActivity(null)}
        onSaved={() => { setPayActivity(null); showToast('Pagamento registrado'); load() }}
      />
    </div>
  )
}

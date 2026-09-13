import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'
import { Card, Field, inputClass } from '../components/ui'
import { useToast } from '../components/Toast'
import { createCharts, destroyCharts, filterActivitiesByPeriod, paidTotal } from '../charts/buildCharts'
import { exportChartImages, exportExcel, exportPdf } from '../charts/exportReports'
import { formatCurrency } from '../format'

export default function GraficosPage() {
  const { obraId } = useParams()
  const { showToast } = useToast()
  const [period, setPeriod] = useState('all')
  const [activities, setActivities] = useState([])
  const [membros, setMembros] = useState([])
  const [error, setError] = useState('')
  const chartsRef = useRef({})
  const canvasRef = useRef({})

  async function load() {
    setError('')
    try {
      const data = await api.get(`/obras/${obraId}/resumo`)
      setActivities(Array.isArray(data.atividades) ? data.atividades : [])
      setMembros(Array.isArray(data.membros) ? data.membros : [])
    } catch (err) {
      setError(err.message || 'Erro ao carregar gráficos')
    }
  }

  useEffect(() => { load() }, [obraId])

  const filtered = useMemo(
    () => filterActivitiesByPeriod(activities, period),
    [activities, period],
  )
  const total = filtered.reduce((sum, activity) => sum + Number(activity.value || 0), 0)
  const pago = filtered.reduce((sum, activity) => sum + paidTotal(activity), 0)
  const pct = total > 0 ? ((pago / total) * 100).toFixed(0) : '0'
  const completed = filtered.filter((activity) => paidTotal(activity) >= activity.value).length

  useEffect(() => {
    destroyCharts(chartsRef.current)
    chartsRef.current = createCharts(canvasRef.current, filtered)
    return () => destroyCharts(chartsRef.current)
  }, [filtered])

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <h2 className="text-xl font-semibold text-blue-800">Gráficos</h2>
        <div className="flex flex-wrap gap-2 items-end">
          <Field label="Período">
            <select className={inputClass()} value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="all">Todo o período</option>
              <option value="month">Último mês</option>
              <option value="quarter">Último trimestre</option>
              <option value="year">Último ano</option>
            </select>
          </Field>
          <button type="button" className="btn-export bg-blue-50 text-blue-800 px-3 py-2 rounded-lg text-sm mb-3" onClick={() => exportPdf({ charts: chartsRef.current, total, pago, activities: filtered }).catch((e) => showToast(e.message, 'error'))}>
            PDF
          </button>
          <button type="button" className="bg-green-50 text-green-800 px-3 py-2 rounded-lg text-sm mb-3" onClick={() => exportExcel({ activities: filtered, total, pago, membros })}>
            Excel
          </button>
          <button type="button" className="bg-purple-50 text-purple-800 px-3 py-2 rounded-lg text-sm mb-3" onClick={() => exportChartImages(chartsRef.current)}>
            Imagens
          </button>
        </div>
      </div>

      {error ? <p className="text-sm text-red-600 mb-3">{error}</p> : null}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
        <Card className="p-4">
          <p className="text-sm text-gray-600">Progresso</p>
          <div className="w-full bg-gray-200 rounded-full h-3 mt-2">
            <div className="bg-blue-600 h-3 rounded-full" style={{ width: `${Math.min(pct, 100)}%` }} />
          </div>
          <p className="text-sm text-blue-800 mt-2">{pct}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Pago</p>
          <p className="text-2xl font-bold text-gray-800">{formatCurrency(pago)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Atividades</p>
          <p className="text-2xl font-bold text-gray-800">{completed}/{filtered.length}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Status das atividades</h3>
          <div className="h-64">
            <canvas ref={(el) => { canvasRef.current.statusChart = el }} />
          </div>
        </Card>
        <Card className="p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Gastos por setor</h3>
          <div className="h-64">
            <canvas ref={(el) => { canvasRef.current.sectorExpenseChart = el }} />
          </div>
        </Card>
        <Card className="p-4 md:col-span-2">
          <h3 className="font-semibold text-gray-700 mb-3">Evolução</h3>
          <div className="h-64">
            <canvas ref={(el) => { canvasRef.current.timelineChart = el }} />
          </div>
        </Card>
      </div>
    </div>
  )
}

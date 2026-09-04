import { Chart } from 'chart.js/auto'

const MEMBER_COLORS = ['#3B82F6', '#FBBF24', '#10B981', '#EF4444', '#8B5CF6', '#F97316']

export function paidTotal(a) {
  return Number(a.total_pago || 0)
}

function parseDate(dateString) {
  if (!dateString) return null
  const parts = String(dateString).split('/')
  if (parts.length !== 3) return null
  return new Date(parseInt(parts[2], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10))
}

export function filterActivitiesByPeriod(activities, periodFilter) {
  if (periodFilter === 'all') return activities
  const now = new Date()
  let cutoffDate
  if (periodFilter === 'month') cutoffDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate())
  else if (periodFilter === 'quarter') cutoffDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate())
  else if (periodFilter === 'year') cutoffDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
  else return activities
  return activities.filter((activity) => {
    const activityDate = parseDate(activity.date)
    return activityDate && activityDate >= cutoffDate
  })
}

const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
}

export function createCharts(canvasMap, activities) {
  const instances = {}
  function make(id, config) {
    const el = canvasMap[id]
    if (!el) return
    instances[id] = new Chart(el, config)
  }

  const pendingCount = activities.filter((a) => paidTotal(a) < a.value).length
  const completedCount = activities.length - pendingCount
  make('statusChart', {
    type: 'pie',
    data: {
      labels: ['Concluídas', 'Pendentes'],
      datasets: [{ data: [completedCount, pendingCount], backgroundColor: ['#10B981', '#FBBF24'] }],
    },
    options: { ...baseOptions, plugins: { legend: { position: 'bottom' } } },
  })

  make('expenseDistributionChart', {
    type: 'bar',
    data: {
      labels: activities.map((a) => a.activity),
      datasets: [{ label: 'Gastos', data: activities.map((a) => a.value), backgroundColor: '#3B82F6' }],
    },
    options: { ...baseOptions, plugins: { legend: { display: false } } },
  })

  make('expenseEvolutionChart', {
    type: 'line',
    data: {
      labels: activities.map((a) => a.date),
      datasets: [{
        label: 'Evolução',
        data: activities.map((a) => a.value),
        borderColor: '#3B82F6',
        backgroundColor: '#3B82F6',
        fill: false,
      }],
    },
    options: { ...baseOptions, plugins: { legend: { display: false } } },
  })

  const memberNames = []
  activities.forEach((a) => {
    (a.pagamentos || []).forEach((p) => {
      if (!memberNames.includes(p.nome)) memberNames.push(p.nome)
    })
  })
  make('paymentComparisonChart', {
    type: 'bar',
    data: {
      labels: activities.map((a) => a.activity),
      datasets: (memberNames.length ? memberNames : ['Pago']).map((name, index) => ({
        label: name,
        data: activities.map((a) => {
          const found = (a.pagamentos || []).find((p) => p.nome === name)
          return found ? Number(found.valor) : (memberNames.length ? 0 : paidTotal(a))
        }),
        backgroundColor: MEMBER_COLORS[index % MEMBER_COLORS.length],
      })),
    },
    options: { ...baseOptions, plugins: { legend: { position: 'top' } } },
  })

  const sectorSums = {}
  const sectorCounts = {}
  activities.forEach((a) => {
    const sector = a.sector || 'Sem setor'
    sectorSums[sector] = (sectorSums[sector] || 0) + a.value
    sectorCounts[sector] = (sectorCounts[sector] || 0) + 1
  })
  make('sectorExpenseChart', {
    type: 'bar',
    data: {
      labels: Object.keys(sectorSums),
      datasets: [{ label: 'Gastos por setor', data: Object.values(sectorSums), backgroundColor: '#3B82F6' }],
    },
    options: { ...baseOptions, plugins: { legend: { display: false } } },
  })
  make('sectorActivityChart', {
    type: 'bar',
    data: {
      labels: Object.keys(sectorCounts),
      datasets: [{ label: 'Atividades por setor', data: Object.values(sectorCounts), backgroundColor: '#3B82F6' }],
    },
    options: { ...baseOptions, plugins: { legend: { display: false } } },
  })

  const sorted = [...activities].sort((a, b) => (parseDate(a.date) || 0) - (parseDate(b.date) || 0))
  let sum = 0
  const cumulative = sorted.map((a) => {
    sum += Number(a.value || 0)
    return sum
  })
  make('timelineChart', {
    type: 'line',
    data: {
      labels: sorted.map((a) => a.date),
      datasets: [
        { label: 'Valor por período', data: sorted.map((a) => a.value), borderColor: '#3B82F6', fill: false },
        { label: 'Acumulado', data: cumulative, borderColor: '#10B981', fill: false },
      ],
    },
    options: { ...baseOptions, plugins: { legend: { position: 'top' } } },
  })

  const totals = {}
  activities.forEach((a) => {
    (a.pagamentos || []).forEach((p) => {
      totals[p.nome] = (totals[p.nome] || 0) + Number(p.valor || 0)
    })
    if (!(a.pagamentos || []).length && paidTotal(a)) {
      totals.Pago = (totals.Pago || 0) + paidTotal(a)
    }
  })
  make('paymentDistributionChart', {
    type: 'pie',
    data: {
      labels: Object.keys(totals).length ? Object.keys(totals) : ['Sem pagamentos'],
      datasets: [{
        data: Object.values(totals).length ? Object.values(totals) : [1],
        backgroundColor: Object.keys(totals).map((_, i) => MEMBER_COLORS[i % MEMBER_COLORS.length]),
      }],
    },
    options: { ...baseOptions, plugins: { legend: { position: 'bottom' } } },
  })

  return instances
}

export function destroyCharts(instances) {
  Object.values(instances || {}).forEach((chart) => chart?.destroy())
}

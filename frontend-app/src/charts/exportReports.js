import { jsPDF } from 'jspdf'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { formatCurrency } from '../format'
import { paidTotal } from './buildCharts'

export async function exportPdf({ charts, total, pago, activities }) {
  const doc = new jsPDF('landscape', 'mm', 'a4')
  doc.setFontSize(18)
  doc.setTextColor(59, 130, 246)
  doc.text('Relatório de Gestão de Gastos de Obra', 20, 20)
  doc.setFontSize(10)
  doc.setTextColor(100, 100, 100)
  doc.text(`Exportado em: ${new Date().toLocaleDateString('pt-BR')}`, 20, 28)
  doc.setFontSize(12)
  doc.setTextColor(0, 0, 0)
  doc.text(`Total: ${formatCurrency(total)}  |  Pago: ${formatCurrency(pago)}  |  Atividades: ${activities.length}`, 20, 40)

  let y = 50
  const ids = ['statusChart', 'expenseDistributionChart', 'timelineChart', 'paymentDistributionChart']
  ids.forEach((id, index) => {
    const chart = charts[id]
    if (!chart) return
    if (index === 2) {
      doc.addPage()
      y = 20
    }
    try {
      doc.addImage(chart.toBase64Image(), 'PNG', index % 2 === 0 ? 20 : 150, y, 120, 70)
      if (index % 2 === 1) y += 80
    } catch {
      /* ignore missing canvas */
    }
  })
  doc.save('Relatorio_Gestao_Gastos_Obra.pdf')
}

export async function exportExcel({ activities, total, pago, membros }) {
  const data = activities.map((activity) => ({
    ID: activity.id,
    Data: activity.date,
    Atividade: activity.activity,
    Setor: activity.sector,
    Valor: activity.value,
    'Total Pago': paidTotal(activity),
    Restante: activity.value - paidTotal(activity),
    Status: paidTotal(activity) >= activity.value ? 'Concluída' : 'Pendente',
  }))
  const resumo = [
    { 'Resumo Financeiro': 'Valor Total', Valor: total },
    { 'Resumo Financeiro': 'Valor Pago', Valor: pago },
    { 'Resumo Financeiro': 'Valor Restante', Valor: total - pago },
    ...(membros || []).map((item) => ({ 'Resumo Financeiro': `Pago ${item.nome}`, Valor: item.total })),
  ]
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(data), 'Atividades')
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(resumo), 'Resumo Financeiro')
  const out = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(new Blob([out], { type: 'application/octet-stream' }), 'Relatorio_Gestao_Gastos_Obra.xlsx')
}

export function exportChartImages(charts) {
  Object.entries(charts || {}).forEach(([id, chart]) => {
    if (!chart) return
    try {
      const dataUrl = chart.toBase64Image()
      const link = document.createElement('a')
      link.href = dataUrl
      link.download = `${id}.png`
      link.click()
    } catch {
      /* ignore */
    }
  })
}

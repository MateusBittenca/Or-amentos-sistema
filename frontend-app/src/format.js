export function formatCurrency(value) {
  return `R$ ${Number(value || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export function parseCurrencyInput(text) {
  if (text == null) return ''
  return String(text)
    .replace('R$', '')
    .replace(/\./g, '')
    .replace(',', '.')
    .trim()
}

export function apiError(data, fallback) {
  if (!data) return fallback
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg || JSON.stringify(item)).join(' ')
  }
  return data.message || fallback
}

import { useEffect, useState } from 'react'
import { api } from '../api'
import { canEditObra, canPayObra, paidTotal, activityValue } from '../constants'
import { formatCurrency, parseCurrencyInput } from '../format'
import { Button, Field, Modal, inputClass } from './ui'
import { useToast } from './Toast'

const MAX_RECEIPT_BYTES = 5 * 1024 * 1024

function StoredReceipt({ pagamento, obraId }) {
  const [src, setSrc] = useState('')

  useEffect(() => {
    if (!pagamento?.id || !pagamento.comprovante_url) return undefined
    let objectUrl = ''
    let cancelled = false
    api.getBlob(`/pagamentos/${pagamento.id}/comprovante`, obraId)
      .then((blob) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setSrc(objectUrl)
      })
      .catch(() => {
        if (!cancelled) setSrc('')
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [pagamento, obraId])

  if (!pagamento?.comprovante_url) return null
  if (!src) return <p className="text-xs text-gray-500 mt-1">Carregando comprovante...</p>
  return <img src={src} alt={`Comprovante de ${pagamento.nome}`} className="mt-2 max-h-32 rounded-lg" />
}

export default function PaymentModal({ activity, obraId, papel, onClose, onSaved }) {
  const { showToast } = useToast()
  const [membros, setMembros] = useState([])
  const [payer, setPayer] = useState(localStorage.getItem('user_id') || '')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [saving, setSaving] = useState(false)
  const [dragging, setDragging] = useState(false)

  const open = Boolean(activity)
  const restante = activity ? activityValue(activity) - paidTotal(activity) : 0
  const alreadyPaid = activity ? restante <= 0 : false
  const canPay = canPayObra(papel || localStorage.getItem('obra_papel'))
  const canChoosePayer = canEditObra(papel || localStorage.getItem('obra_papel'))
  const storedPayments = (activity?.pagamentos || []).filter((item) => item.comprovante_url)

  useEffect(() => {
    if (!open) return
    setFile(null)
    setPreview('')
    setDragging(false)
    setPayer(localStorage.getItem('user_id') || '')
    api.get(`/obras/${obraId}/membros`).then((data) => {
      setMembros(Array.isArray(data) ? data : [])
    }).catch(() => setMembros([]))
  }, [open, obraId])

  function applyFile(selected) {
    if (!selected) {
      setFile(null)
      setPreview('')
      return
    }
    if (!String(selected.type || '').startsWith('image/')) {
      showToast('Envie uma imagem (jpg, png ou similar)', 'error')
      return
    }
    if (selected.size > MAX_RECEIPT_BYTES) {
      showToast('O comprovante deve ter no máximo 5 MB', 'error')
      return
    }
    setFile(selected)
    const reader = new FileReader()
    reader.onload = (ev) => setPreview(ev.target.result)
    reader.readAsDataURL(selected)
  }

  function onFile(e) {
    applyFile(e.target.files?.[0] || null)
    e.target.value = ''
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    applyFile(e.dataTransfer.files?.[0] || null)
  }

  function clearFile(e) {
    e.preventDefault()
    e.stopPropagation()
    setFile(null)
    setPreview('')
  }

  async function confirm() {
    if (!activity) return
    setSaving(true)
    try {
      const maxValue = Math.round(Math.max(restante, 0) * 100) / 100
      let value = maxValue
      let date = new Date().toISOString().split('T')[0]
      if (file) {
        const ocrForm = new FormData()
        ocrForm.append('file', file)
        const extracted = await api.postForm('/process-receipt', ocrForm, obraId)
        if (extracted.value) {
          const extractedValue = Math.round(Number(parseCurrencyInput(extracted.value) || value) * 100) / 100
          if (extractedValue > maxValue) {
            showToast('O valor do comprovante foi limitado ao restante da atividade')
            value = maxValue
          } else {
            value = extractedValue
          }
        }
        if (extracted.date) date = extracted.date
      }
      const form = new FormData()
      form.append('atividade_id', String(activity.id))
      form.append('usuario_id', String(parseInt(payer, 10)))
      form.append('value', String(value))
      form.append('date', date)
      if (file) form.append('file', file)
      await api.postForm('/register-payment', form, obraId)
      onSaved()
    } catch (err) {
      showToast(err.message || 'Erro ao registrar pagamento', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title={alreadyPaid ? 'Detalhes da atividade' : 'Registrar pagamento'}
      onClose={onClose}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose}>Fechar</Button>
          {!alreadyPaid && canPay ? (
            <Button loading={saving} onClick={confirm}>Confirmar pagamento</Button>
          ) : null}
        </>
      )}
    >
      {activity ? (
        <div className="space-y-3 text-sm">
          <p><span className="text-gray-600">Atividade:</span> {activity.activity}</p>
          <p><span className="text-gray-600">Setor:</span> {activity.sector || '-'}</p>
          <p><span className="text-gray-600">Valor total:</span> {formatCurrency(activityValue(activity))}</p>
          <p><span className="text-gray-600">Pago:</span> {formatCurrency(paidTotal(activity))}</p>
          <p><span className="text-gray-600">Pendente:</span> {formatCurrency(Math.max(restante, 0))}</p>
          {(activity.pagamentos || []).length > 0 ? (
            <div className="space-y-2">
              {(activity.pagamentos || []).map((pagamento) => (
                <div key={pagamento.id || `${pagamento.usuario_id}-${pagamento.valor}`} className="rounded-lg bg-gray-50 p-3">
                  <p className="text-gray-700">{pagamento.nome}: {formatCurrency(pagamento.valor)}</p>
                  <StoredReceipt pagamento={pagamento} obraId={obraId} />
                </div>
              ))}
            </div>
          ) : null}

          {!alreadyPaid && canPay ? (
            <>
              <Field label="Quem está pagando?">
                <select className={inputClass()} value={payer} onChange={(e) => setPayer(e.target.value)}>
                  {(canChoosePayer ? membros : membros.filter((m) => String(m.usuario_id) === String(localStorage.getItem('user_id')))).map((membro) => (
                    <option key={membro.usuario_id} value={membro.usuario_id}>{membro.nome}</option>
                  ))}
                </select>
              </Field>
              <div>
                <p className="text-sm text-gray-600 mb-1">Comprovante (opcional, OCR)</p>
                {preview ? (
                  <div className="rounded-xl border-2 border-blue-200 bg-blue-50 p-4 text-center">
                    <img src={preview} alt="Comprovante" className="mx-auto max-h-40 rounded-lg" />
                    <p className="mt-2 text-xs text-gray-600 truncate">{file?.name}</p>
                    <div className="mt-3 flex items-center justify-center gap-3">
                      <label className="cursor-pointer text-sm text-blue-700 hover:text-blue-800">
                        <input type="file" accept="image/*" className="hidden" onChange={onFile} />
                        Trocar imagem
                      </label>
                      <button type="button" className="text-sm text-red-600 hover:text-red-700" onClick={clearFile}>
                        Remover
                      </button>
                    </div>
                  </div>
                ) : (
                  <label
                    className={`block cursor-pointer rounded-xl border-2 border-dashed p-5 text-center transition-colors ${
                      dragging
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
                    }`}
                    onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={onDrop}
                  >
                    <input type="file" accept="image/*" className="hidden" onChange={onFile} />
                    <span className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-100 text-blue-600 mb-2">
                      <i className="fas fa-image text-xl" />
                    </span>
                    <p className="text-sm font-medium text-blue-800">Clique ou arraste a imagem</p>
                    <p className="text-xs text-gray-500 mt-1">JPG, PNG ou WebP até 5 MB — o valor pode ser lido automaticamente</p>
                  </label>
                )}
              </div>
            </>
          ) : null}
          {alreadyPaid && storedPayments.length === 0 ? (
            <p className="text-xs text-gray-500">Nenhum comprovante anexado a estes pagamentos.</p>
          ) : null}
        </div>
      ) : null}
    </Modal>
  )
}

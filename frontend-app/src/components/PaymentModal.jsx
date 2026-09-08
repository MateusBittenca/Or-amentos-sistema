import { useEffect, useState } from 'react'
import { api } from '../api'
import { canEditObra, canPayObra, paidTotal, activityValue } from '../constants'
import { formatCurrency, parseCurrencyInput } from '../format'
import { Button, Field, Modal, inputClass } from './ui'
import { useToast } from './Toast'

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
      let value = restante
      let date = new Date().toISOString().split('T')[0]
      if (file) {
        const form = new FormData()
        form.append('file', file)
        const extracted = await api.postForm('/process-receipt', form, obraId)
        if (extracted.value) value = parseCurrencyInput(extracted.value) || value
        if (extracted.date) date = extracted.date
      }
      await api.postJson('/register-payment', {
        activity: activity.activity,
        sector: activity.sector || null,
        usuario_id: parseInt(payer, 10),
        value: String(value),
        date,
      }, obraId)
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
            <p className="text-gray-600">
              Pagamentos: {(activity.pagamentos || []).map((p) => `${p.nome}: ${formatCurrency(p.valor)}`).join(' | ')}
            </p>
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
                    <p className="text-xs text-gray-500 mt-1">JPG, PNG — o valor pode ser lido automaticamente</p>
                  </label>
                )}
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </Modal>
  )
}

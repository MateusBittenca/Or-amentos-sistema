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

  const open = Boolean(activity)
  const restante = activity ? activityValue(activity) - paidTotal(activity) : 0
  const alreadyPaid = activity ? restante <= 0 : false
  const canPay = canPayObra(papel || localStorage.getItem('obra_papel'))
  const canChoosePayer = canEditObra(papel || localStorage.getItem('obra_papel'))

  useEffect(() => {
    if (!open) return
    setFile(null)
    setPreview('')
    setPayer(localStorage.getItem('user_id') || '')
    api.get(`/obras/${obraId}/membros`).then((data) => {
      setMembros(Array.isArray(data) ? data : [])
    }).catch(() => setMembros([]))
  }, [open, obraId])

  function onFile(e) {
    const selected = e.target.files?.[0]
    setFile(selected || null)
    if (selected) {
      const reader = new FileReader()
      reader.onload = (ev) => setPreview(ev.target.result)
      reader.readAsDataURL(selected)
    } else {
      setPreview('')
    }
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
              <Field label="Comprovante (opcional, OCR)">
                <input type="file" accept="image/*" onChange={onFile} />
              </Field>
              {preview ? <img src={preview} alt="Comprovante" className="max-h-40 rounded-lg" /> : null}
            </>
          ) : null}
        </div>
      ) : null}
    </Modal>
  )
}

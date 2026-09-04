import { useEffect, useState } from 'react'
import { api } from '../api'
import { SECTORS } from '../constants'
import { Button, Field, Modal, inputClass } from './ui'
import { useToast } from './Toast'

export default function ActivityFormModal({ open, obraId, onClose, onSaved, activity }) {
  const { showToast } = useToast()
  const [atividade, setAtividade] = useState(activity?.activity || '')
  const [valor, setValor] = useState(activity?.value || activity?.total_value || '')
  const [setor, setSetor] = useState(activity?.sector || '')
  const [data, setData] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setAtividade(activity?.activity || '')
    setValor(activity?.value || activity?.total_value || '')
    setSetor(activity?.sector || '')
    setData('')
  }, [open, activity])

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const form = new FormData()
      form.append('atividade', atividade)
      form.append('valor', String(valor))
      form.append('setor', setor)
      form.append('data', data)
      if (activity?.id) {
        await api.putForm(`/edit-activity/${activity.id}`, form, obraId)
      } else {
        await api.postForm('/add-activity', form, obraId)
      }
      onSaved()
    } catch (err) {
      showToast(err.message || 'Erro ao salvar atividade', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title={activity ? 'Editar atividade' : 'Adicionar atividade'}
      onClose={onClose}
      footer={(
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button type="submit" form="activityForm" loading={saving}>Salvar</Button>
        </>
      )}
    >
      <form id="activityForm" onSubmit={submit} className="grid grid-cols-1 md:grid-cols-2 gap-1">
        <div className="md:col-span-2">
          <Field label="Atividade">
            <input className={inputClass()} value={atividade} onChange={(e) => setAtividade(e.target.value)} required />
          </Field>
        </div>
        <Field label="Valor (R$)">
          <input className={inputClass()} type="number" step="0.01" value={valor} onChange={(e) => setValor(e.target.value)} required />
        </Field>
        <Field label="Data para pagar">
          <input className={inputClass()} type="date" value={data} onChange={(e) => setData(e.target.value)} required />
        </Field>
        <div className="md:col-span-2">
          <Field label="Setor">
            <select className={inputClass()} value={setor} onChange={(e) => setSetor(e.target.value)} required>
              <option value="">Escolha uma opção</option>
              {SECTORS.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </Field>
        </div>
      </form>
    </Modal>
  )
}

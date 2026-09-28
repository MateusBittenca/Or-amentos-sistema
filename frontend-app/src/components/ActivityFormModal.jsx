import { useEffect, useState } from 'react'
import { api } from '../api'
import { SECTORS } from '../constants'
import { Button, Field, Modal, inputClass } from './ui'
import { useToast } from './Toast'

function toDateInput(value) {
  if (!value) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  const match = String(value).match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (match) return `${match[3]}-${match[2]}-${match[1]}`
  return ''
}

function percentCents(value) {
  const number = Number(String(value ?? '').replace(',', '.'))
  if (!Number.isFinite(number)) return 0
  return Math.round(number * 100)
}

function montarLinhas(membros, frozen) {
  const rows = []
  const seen = new Set()
  ;(frozen || []).forEach((item) => {
    seen.add(item.usuario_id)
    const member = membros.find((membro) => membro.usuario_id === item.usuario_id)
    rows.push({
      usuario_id: item.usuario_id,
      nome: member?.nome || item.nome,
      percentual: String(item.percentual),
    })
  })
  membros.forEach((membro) => {
    if (membro.papel === 'leitura' || seen.has(membro.usuario_id)) return
    rows.push({
      usuario_id: membro.usuario_id,
      nome: membro.nome,
      percentual: frozen?.length ? '' : (membro.participacao == null ? '' : String(membro.participacao)),
    })
  })
  return rows
}

export default function ActivityFormModal({ open, obraId, onClose, onSaved, activity }) {
  const { showToast } = useToast()
  const [atividade, setAtividade] = useState(activity?.activity || '')
  const [valor, setValor] = useState(activity?.value || activity?.total_value || '')
  const [setor, setSetor] = useState(activity?.sector || '')
  const [data, setData] = useState('')
  const [saving, setSaving] = useState(false)
  const [seguir, setSeguir] = useState(true)
  const [linhas, setLinhas] = useState([])

  useEffect(() => {
    if (!open) return
    setAtividade(activity?.activity || '')
    setValor(activity?.value || activity?.total_value || '')
    setSetor(activity?.sector || '')
    setData(toDateInput(activity?.date))
    setSeguir(!activity?.id)
    setLinhas([])
    api.get(`/obras/${obraId}/membros`).then((data) => {
      const members = Array.isArray(data) ? data : []
      setLinhas(montarLinhas(members, activity?.participacao))
    }).catch(() => setLinhas([]))
  }, [open, activity, obraId])

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const form = new FormData()
      form.append('atividade', atividade)
      form.append('valor', String(valor))
      form.append('setor', setor)
      form.append('data', data)
      if (seguir) {
        form.append('participacao', 'obra')
      } else {
        const soma = linhas.reduce((total, linha) => total + percentCents(linha.percentual), 0)
        if (soma !== 10000) {
          showToast('A soma da participação deve ser 100%', 'error')
          setSaving(false)
          return
        }
        form.append('participacao', JSON.stringify(linhas.map((linha) => ({
          usuario_id: linha.usuario_id,
          percentual: Number(String(linha.percentual).replace(',', '.')),
        }))))
      }
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
        <div className="md:col-span-2">
          <label className="flex items-center gap-2 text-sm text-gray-700 mb-2">
            <input type="checkbox" checked={seguir} onChange={(e) => setSeguir(e.target.checked)} />
            Seguir participação da obra
          </label>
          {seguir ? (
            <p className="text-xs text-gray-500 mb-3">Usa os percentuais atuais da equipe. Leitura não entra.</p>
          ) : (
            <div className="space-y-2 mb-3">
              {linhas.map((linha) => (
                <div key={linha.usuario_id} className="flex items-center justify-between gap-3">
                  <span className="text-sm text-gray-700 truncate">{linha.nome}</span>
                  <input
                    className="input-focus w-24 px-2 py-1 border rounded-lg text-sm"
                    type="number"
                    min="0"
                    max="100"
                    step="0.01"
                    value={linha.percentual}
                    aria-label={`Participação de ${linha.nome}`}
                    onChange={(e) => {
                      const value = e.target.value
                      setLinhas((current) => current.map((item) => (
                        item.usuario_id === linha.usuario_id ? { ...item, percentual: value } : item
                      )))
                    }}
                  />
                </div>
              ))}
              <p className={`text-xs ${linhas.reduce((total, linha) => total + percentCents(linha.percentual), 0) === 10000 ? 'text-gray-500' : 'text-red-600'}`}>
                Soma {(linhas.reduce((total, linha) => total + percentCents(linha.percentual), 0) / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%
              </p>
            </div>
          )}
        </div>
      </form>
    </Modal>
  )
}

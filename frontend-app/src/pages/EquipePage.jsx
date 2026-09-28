import { useEffect, useState } from 'react'
import { useOutletContext, useParams } from 'react-router-dom'
import { api } from '../api'
import { canEditObra, isObraOwner, ROLE_HINTS, ROLE_INVITE_OPTIONS, roleLabel } from '../constants'
import { Button, Card, EmptyState, Field, inputClass } from '../components/ui'
import { useToast } from '../components/Toast'

function percentCents(value) {
  const number = Number(String(value ?? '').replace(',', '.'))
  if (!Number.isFinite(number)) return 0
  return Math.round(number * 100)
}

function formatPercent(cents) {
  return `${(cents / 100).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
}

export default function EquipePage() {
  const { obraId } = useParams()
  const { obra } = useOutletContext()
  const { showToast } = useToast()
  const [membros, setMembros] = useState([])
  const [papel, setPapel] = useState('membro')
  const [inviteUrl, setInviteUrl] = useState('')
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [percents, setPercents] = useState({})
  const [savingShare, setSavingShare] = useState(false)
  const currentPapel = obra?.papel || localStorage.getItem('obra_papel')
  const canInvite = canEditObra(currentPapel)
  const owner = isObraOwner(currentPapel)

  async function load() {
    setError('')
    try {
      const data = await api.get(`/obras/${obraId}/membros`)
      const list = Array.isArray(data) ? data : []
      setMembros(list)
      const next = {}
      list.forEach((membro) => {
        if (membro.papel !== 'leitura' && membro.participacao != null) {
          next[membro.usuario_id] = String(membro.participacao)
        }
      })
      setPercents(next)
    } catch (err) {
      setError(err.message || 'Erro ao carregar equipe')
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => { load() }, [obraId])

  async function gerarConvite() {
    try {
      const data = await api.postJson(`/obras/${obraId}/convites`, { papel })
      const url = `${window.location.origin}/convite/${data.token}`
      setInviteUrl(url)
      try {
        await navigator.clipboard.writeText(url)
        showToast('Link copiado')
      } catch {
        showToast('Link gerado')
      }
    } catch (err) {
      showToast(err.message || 'Erro ao gerar convite', 'error')
    }
  }

  async function changePapel(membroId, next) {
    try {
      await api.patchJson(`/obras/${obraId}/membros/${membroId}`, { papel: next })
      showToast('Papel atualizado')
      load()
    } catch (err) {
      showToast(err.message || 'Erro ao alterar papel', 'error')
    }
  }

  async function salvarParticipacao() {
    const participantes = membros
      .filter((membro) => membro.papel !== 'leitura')
      .map((membro) => ({
        usuario_id: membro.usuario_id,
        percentual: Number(String(percents[membro.usuario_id] ?? '').replace(',', '.')),
      }))
    const soma = participantes.reduce((total, item) => total + percentCents(item.percentual), 0)
    if (soma !== 10000) {
      showToast('A soma da participação deve ser 100%', 'error')
      return
    }
    setSavingShare(true)
    try {
      await api.patchJson(`/obras/${obraId}/participacao`, { participantes })
      showToast('Participação atualizada')
      load()
    } catch (err) {
      showToast(err.message || 'Erro ao salvar participação', 'error')
    } finally {
      setSavingShare(false)
    }
  }

  async function remove(membroId) {
    if (!window.confirm('Remover este membro?')) return
    try {
      await api.del(`/obras/${obraId}/membros/${membroId}`)
      showToast('Membro removido')
      load()
    } catch (err) {
      showToast(err.message || 'Erro ao remover', 'error')
    }
  }

  const rateio = membros.filter((membro) => membro.papel !== 'leitura')
  const soma = rateio.reduce((total, membro) => total + percentCents(percents[membro.usuario_id]), 0)

  function participacaoCell(membro) {
    if (membro.papel === 'leitura') {
      return <span className="text-xs text-gray-500">Não entra no rateio</span>
    }
    if (!owner) {
      return <span className="text-sm text-gray-700">{membro.participacao != null ? `${membro.participacao}%` : '—'}</span>
    }
    return (
      <input
        className="input-focus w-24 px-2 py-1 border rounded-lg text-sm"
        type="number"
        min="0"
        max="100"
        step="0.01"
        value={percents[membro.usuario_id] ?? ''}
        onChange={(e) => setPercents((current) => ({ ...current, [membro.usuario_id]: e.target.value }))}
        aria-label={`Participação de ${membro.nome}`}
      />
    )
  }

  return (
    <div>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
        <h2 className="text-xl font-semibold text-blue-800">Equipe</h2>
        {canInvite ? (
          <div>
            <div className="flex flex-col sm:flex-row sm:items-end gap-2">
              <Field label="Papel do convite">
                <select className={inputClass()} value={papel} onChange={(e) => setPapel(e.target.value)}>
                  {ROLE_INVITE_OPTIONS.map((item) => (
                    <option key={item} value={item}>{roleLabel(item)}</option>
                  ))}
                </select>
              </Field>
              <Button onClick={gerarConvite} className="mb-3">Gerar convite</Button>
            </div>
            <p className="text-xs text-gray-500 -mt-2">{ROLE_HINTS[papel]}</p>
          </div>
        ) : null}
      </div>

      {inviteUrl ? (
        <p className="mb-4 p-3 bg-blue-50 text-blue-800 rounded-lg break-all text-sm">{inviteUrl}</p>
      ) : null}
      {error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null}

      <Card className="overflow-hidden">
        {!loaded ? (
          <p className="text-sm text-gray-500 p-4">Carregando...</p>
        ) : membros.length <= 1 ? (
          <div className="p-4">
            <EmptyState icon="fa-user-friends" text="Só você nesta obra. Gere um convite para chamar alguém." />
            {membros.length === 1 ? (
              <p className="text-center text-sm text-gray-600 -mt-4 mb-2">{membros[0].nome} · {roleLabel(membros[0].papel)}</p>
            ) : null}
          </div>
        ) : (
          <>
            <p className="px-4 pt-4 text-xs text-gray-500">
              Atividades novas usam estes percentuais. As que já existem não mudam. Leitura não entra no rateio.
            </p>
            <div className="sm:hidden divide-y divide-gray-100">
              {membros.map((membro) => (
                <div key={membro.usuario_id} className="px-4 py-4">
                  <p className="font-medium text-gray-800 break-all">{membro.nome}</p>
                  <div className="mt-2">{participacaoCell(membro)}</div>
                  <div className="mt-3 flex items-center gap-2">
                    {owner && membro.papel !== 'owner' ? (
                      <select
                        className="input-focus flex-1 px-2 py-2 border rounded-lg text-sm"
                        value={membro.papel}
                        onChange={(e) => changePapel(membro.usuario_id, e.target.value)}
                      >
                        {ROLE_INVITE_OPTIONS.map((item) => (
                          <option key={item} value={item}>{roleLabel(item)}</option>
                        ))}
                      </select>
                    ) : (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-800">{roleLabel(membro.papel)}</span>
                    )}
                    {owner && membro.papel !== 'owner' ? (
                      <button type="button" className="text-red-600 text-sm font-medium px-3 py-2 rounded-lg hover:bg-red-50 shrink-0" onClick={() => remove(membro.usuario_id)}>
                        Remover
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                  <tr>
                    <th className="text-left font-medium py-3 px-4">Membro</th>
                    <th className="text-left font-medium py-3 px-4">Papel</th>
                    <th className="text-left font-medium py-3 px-4">Participação</th>
                    <th className="text-right font-medium py-3 px-4">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {membros.map((membro) => (
                    <tr key={membro.usuario_id} className="hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-800">{membro.nome}</td>
                      <td className="py-3 px-4">
                        {owner && membro.papel !== 'owner' ? (
                          <select
                            className="input-focus px-2 py-1 border rounded-lg"
                            value={membro.papel}
                            onChange={(e) => changePapel(membro.usuario_id, e.target.value)}
                          >
                            {ROLE_INVITE_OPTIONS.map((item) => (
                              <option key={item} value={item}>{roleLabel(item)}</option>
                            ))}
                          </select>
                        ) : (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-800">{roleLabel(membro.papel)}</span>
                        )}
                      </td>
                      <td className="py-3 px-4">{participacaoCell(membro)}</td>
                      <td className="py-3 px-4 text-right">
                        {owner && membro.papel !== 'owner' ? (
                          <button type="button" className="text-red-600 text-sm font-medium hover:bg-red-50 px-3 py-1.5 rounded-lg" onClick={() => remove(membro.usuario_id)}>Remover</button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {owner ? (
              <div className="px-4 py-3 border-t flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <p className={`text-sm ${soma === 10000 ? 'text-gray-600' : 'text-red-600'}`}>Soma {formatPercent(soma)}</p>
                <Button onClick={salvarParticipacao} loading={savingShare}>Salvar participação</Button>
              </div>
            ) : null}
          </>
        )}
      </Card>
    </div>
  )
}

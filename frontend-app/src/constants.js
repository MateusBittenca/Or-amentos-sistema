export const SECTORS = [
  'Documentação',
  'Financiamento',
  'Advocacia',
  'Projeto',
  'Materiais',
  'Serviços',
  'Projetos',
  'Depósito',
  'Metal',
  'Marmoraria',
  'Manutenção',
  'Construtor',
  'Telhado',
  'Piso e Revestimento',
  'Louça',
  'Aluguel Equipamento',
  'Areia e Pedra',
  'Esquadrias',
  'Gesso',
  'Limpeza',
  'Paisagismo',
  'Portão',
  'Marcenaria',
  'Energia',
  'Água',
  'Condomínio',
  'Impostos',
  'Cimento e Concreto',
  'Hidráulica',
  'Elétrica',
  'Blocos e Tijolos',
  'Ferro',
  'Iluminação',
]

export function canEditObra(papel) {
  return papel === 'owner' || papel === 'editor'
}

export function canPayObra(papel) {
  return papel === 'owner' || papel === 'editor' || papel === 'membro'
}

export function isObraOwner(papel) {
  return papel === 'owner'
}

export function paidTotal(activity) {
  if (activity.total_pago != null) return Number(activity.total_pago)
  return (activity.pagamentos || []).reduce((sum, p) => sum + Number(p.valor || 0), 0)
}

export function activityValue(activity) {
  return Number(activity.value ?? activity.total_value ?? 0)
}

export function isPaid(activity) {
  if (activity.status === 'paid') return true
  return paidTotal(activity) >= activityValue(activity) && activityValue(activity) > 0
}

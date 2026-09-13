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

export const ROLE_LABELS = {
  owner: 'Dono',
  editor: 'Editor',
  membro: 'Membro',
  leitura: 'Somente leitura',
}

export const ROLE_HINTS = {
  owner: 'Acesso total',
  editor: 'Pode cadastrar e editar atividades',
  membro: 'Pode registrar os próprios pagamentos',
  leitura: 'Só visualiza',
}

export const ROLE_INVITE_OPTIONS = ['editor', 'membro', 'leitura']

export function roleLabel(papel) {
  return ROLE_LABELS[papel] || papel
}

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

export function paymentStatus(activity) {
  if (!activity) return 'pending'
  const paid = paidTotal(activity)
  const value = activityValue(activity)
  if (activity.status === 'paid' || (value > 0 && paid >= value)) return 'paid'
  if (paid > 0 && paid < value) return 'partial'
  return 'pending'
}

export function isPaid(activity) {
  return paymentStatus(activity) === 'paid'
}

import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'

const links = [
  { to: '', label: 'Resumo', icon: 'fa-home', end: true },
  { to: 'atividades', label: 'Atividades', icon: 'fa-list-ul' },
  { to: 'graficos', label: 'Gráficos', icon: 'fa-chart-line' },
  { to: 'equipe', label: 'Equipe', icon: 'fa-user-friends' },
]

export default function ObraLayout() {
  const { obraId } = useParams()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [obra, setObra] = useState(null)
  const [menu, setMenu] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await api.get(`/obras/${obraId}`)
        if (cancelled) return
        setObra(data)
        localStorage.setItem('obra_id', String(data.id))
        localStorage.setItem('obra_papel', data.papel)
        localStorage.setItem('obra_nome', data.nome)
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Obra não encontrada')
          if (err.status === 403 || err.status === 404) navigate('/obras', { replace: true })
        }
      }
    }
    load()
    return () => { cancelled = true }
  }, [obraId, navigate])

  const base = `/obras/${obraId}`
  const linkClass = ({ isActive }) =>
    `nav-link inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${isActive ? 'bg-white bg-opacity-20' : 'hover:bg-white hover:bg-opacity-10'}`

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-blue-800 text-white shadow-md">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <h1 className="font-bold flex items-center">
              <i className="fas fa-hard-hat mr-2" />Gestão de Gastos
            </h1>
            {obra ? (
              <p className="text-xs text-blue-200 truncate">{obra.nome} · {obra.papel}</p>
            ) : null}
          </div>
          <div className="flex items-center gap-1 flex-wrap">
            {links.map((item) => (
              <NavLink key={item.label} to={item.to ? `${base}/${item.to}` : base} end={item.end} className={linkClass}>
                <i className={`fas ${item.icon}`} />
                <span className="hidden sm:inline">{item.label}</span>
              </NavLink>
            ))}
          </div>
          <div className="relative">
            <button
              type="button"
              className="flex items-center gap-2 bg-white bg-opacity-10 hover:bg-opacity-20 rounded-full px-3 py-1.5 text-sm"
              onClick={() => setMenu((open) => !open)}
            >
              <i className="fas fa-user-circle" />
              <span className="hidden sm:inline">{user?.nome}</span>
              <i className="fas fa-chevron-down text-xs" />
            </button>
            {menu ? (
              <div className="absolute right-0 mt-2 w-48 bg-white text-gray-800 rounded-lg shadow-lg z-20">
                <button type="button" className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-100" onClick={() => navigate('/obras')}>
                  Minhas obras
                </button>
                <button type="button" className="block w-full text-left px-4 py-2 text-sm hover:bg-gray-100" onClick={logout}>
                  Sair
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </nav>
      <div className="container mx-auto px-4 py-6 flex-grow">
        {error ? <p className="text-red-600 mb-4">{error}</p> : null}
        <Outlet context={{ obra, setObra }} />
      </div>
    </div>
  )
}

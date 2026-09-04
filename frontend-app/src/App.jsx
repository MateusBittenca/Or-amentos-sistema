import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, RequireAuth } from './auth'
import { ToastProvider } from './components/Toast'
import ObraLayout from './layouts/ObraLayout'
import LoginPage from './pages/LoginPage'
import ObrasPage from './pages/ObrasPage'
import ConvitePage from './pages/ConvitePage'
import ResumoPage from './pages/ResumoPage'
import AtividadesPage from './pages/AtividadesPage'
import GraficosPage from './pages/GraficosPage'
import EquipePage from './pages/EquipePage'

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/convite/:token" element={<ConvitePage />} />
            <Route element={<RequireAuth />}>
              <Route path="/obras" element={<ObrasPage />} />
              <Route path="/obras/:obraId" element={<ObraLayout />}>
                <Route index element={<ResumoPage />} />
                <Route path="atividades" element={<AtividadesPage />} />
                <Route path="graficos" element={<GraficosPage />} />
                <Route path="equipe" element={<EquipePage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  )
}

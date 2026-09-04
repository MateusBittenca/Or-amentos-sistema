import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

function htmlBypass(req) {
  const accept = req.headers.accept || ''
  if (accept.includes('text/html') && !accept.trim().startsWith('application/json')) {
    return '/index.html'
  }
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/token': { target: 'http://127.0.0.1:8000' },
      '/register': { target: 'http://127.0.0.1:8000' },
      '/health': { target: 'http://127.0.0.1:8000' },
      '/atividades': { target: 'http://127.0.0.1:8000' },
      '/atividades-pendentes': { target: 'http://127.0.0.1:8000' },
      '/atividades-pagas': { target: 'http://127.0.0.1:8000' },
      '/add-activity': { target: 'http://127.0.0.1:8000' },
      '/delete-activity': { target: 'http://127.0.0.1:8000' },
      '/edit-activity': { target: 'http://127.0.0.1:8000' },
      '/update-status': { target: 'http://127.0.0.1:8000' },
      '/valor-total': { target: 'http://127.0.0.1:8000' },
      '/valor-total-pago': { target: 'http://127.0.0.1:8000' },
      '/valor-pago-membros': { target: 'http://127.0.0.1:8000' },
      '/process-receipt': { target: 'http://127.0.0.1:8000' },
      '/register-payment': { target: 'http://127.0.0.1:8000' },
      '/password': { target: 'http://127.0.0.1:8000' },
      '/obras': { target: 'http://127.0.0.1:8000', bypass: htmlBypass },
      '/convite': { target: 'http://127.0.0.1:8000', bypass: htmlBypass },
    },
  },
})

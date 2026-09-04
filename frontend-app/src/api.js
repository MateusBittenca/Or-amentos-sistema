import { apiError } from './format'

const JSON_HEADERS = { Accept: 'application/json' }

function token() {
  return localStorage.getItem('access_token')
}

function authHeaders(extra) {
  const headers = {
    ...JSON_HEADERS,
    Authorization: `Bearer ${token()}`,
  }
  return extra ? Object.assign(headers, extra) : headers
}

function withObraQuery(path, obraId) {
  if (!obraId) return path
  const sep = path.includes('?') ? '&' : '?'
  return `${path}${sep}obra_id=${encodeURIComponent(obraId)}`
}

async function parseResponse(response) {
  const text = await response.text()
  const data = text ? JSON.parse(text) : {}
  if (!response.ok) {
    const error = new Error(apiError(data, `Erro ${response.status}`))
    error.status = response.status
    error.data = data
    throw error
  }
  return data
}

export const api = {
  withObraQuery,
  authHeaders,

  async login(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    const response = await fetch('/token', {
      method: 'POST',
      headers: { ...JSON_HEADERS, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    })
    return parseResponse(response)
  },

  async register(nome, password) {
    const response = await fetch('/register', {
      method: 'POST',
      headers: { ...JSON_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome, password }),
    })
    return parseResponse(response)
  },

  async requestPasswordReset(username) {
    const response = await fetch('/password/request-reset', {
      method: 'POST',
      headers: { ...JSON_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    })
    return parseResponse(response)
  },

  async resetPassword(username, reset_token, new_password) {
    const response = await fetch('/password/reset', {
      method: 'POST',
      headers: { ...JSON_HEADERS, 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, reset_token, new_password }),
    })
    return parseResponse(response)
  },

  async get(path, obraId) {
    const response = await fetch(withObraQuery(path, obraId), { headers: authHeaders() })
    return parseResponse(response)
  },

  async postJson(path, body, obraId) {
    const response = await fetch(withObraQuery(path, obraId), {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    })
    return parseResponse(response)
  },

  async patchJson(path, body) {
    const response = await fetch(path, {
      method: 'PATCH',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    })
    return parseResponse(response)
  },

  async del(path, obraId) {
    const response = await fetch(withObraQuery(path, obraId), {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return parseResponse(response)
  },

  async postForm(path, formData, obraId) {
    const response = await fetch(withObraQuery(path, obraId), {
      method: 'POST',
      headers: authHeaders(),
      body: formData,
    })
    return parseResponse(response)
  },

  async putForm(path, formData, obraId) {
    const response = await fetch(withObraQuery(path, obraId), {
      method: 'PUT',
      headers: authHeaders(),
      body: formData,
    })
    return parseResponse(response)
  },

  async getPublic(path) {
    const response = await fetch(path, { headers: JSON_HEADERS })
    return parseResponse(response)
  },
}

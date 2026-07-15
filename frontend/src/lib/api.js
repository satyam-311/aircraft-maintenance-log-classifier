export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const BASE = API_BASE

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const err = new Error(body.detail || `Request failed: ${res.status}`)
    err.status = res.status
    throw err
  }
  return res.json()
}

export const api = {
  classify: (narrative_text) =>
    request('/classify', { method: 'POST', body: JSON.stringify({ narrative_text }) }),

  search: ({ q = '', system, severity, limit = 20 }) => {
    const params = new URLSearchParams({ q, limit: String(limit) })
    if (system) params.set('system', system)
    if (severity) params.set('severity', severity)
    return request(`/search?${params.toString()}`)
  },

  submitCorrection: (report_id, field_corrected, corrected_value) =>
    request('/corrections', {
      method: 'POST',
      body: JSON.stringify({ report_id, field_corrected, corrected_value }),
    }),

  ask: (question) =>
    request('/ask', { method: 'POST', body: JSON.stringify({ question }) }),

  stats: () => request('/stats'),

  modelPerformance: () => request('/model-performance'),

  health: () => request('/health'),
}

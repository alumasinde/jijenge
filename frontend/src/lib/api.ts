import type { Branding, Service, ServiceCategory, ServiceList } from '../types'

const configuredBase = String(import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '')
const API_BASE_URL = configuredBase || '/api/v1'

function apiUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const url = apiUrl(path)
  let response: Response

  try {
    response = await fetch(url, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new Error(`Unable to reach the Jijenge API at ${url}`)
  }

  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.json() as { detail?: string }
      detail = body?.detail ? `: ${body.detail}` : ''
    } catch {
      // Ignore non-JSON error responses.
    }
    throw new Error(`API request failed (${response.status})${detail}`)
  }

  return response.json() as Promise<T>
}

export const api = {
  baseUrl: API_BASE_URL,
  branding: (signal?: AbortSignal) => get<Branding>('/branding', signal),
  categories: (signal?: AbortSignal) => get<ServiceCategory[]>('/services/categories', signal),
  services: (signal?: AbortSignal) => get<ServiceList>('/services', signal),
}

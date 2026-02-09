async function getCsrf(): Promise<string | null> {
  const name = 'csrftoken'
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

export async function api<T>(
  path: string,
  opts: RequestInit & { params?: Record<string, string> } = {}
): Promise<T> {
  const { params, ...init } = opts
  const url = new URL(path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== '') url.searchParams.set(k, String(v))
    })
  }
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  }
  const csrf = await getCsrf()
  if (csrf) headers['X-CSRFToken'] = csrf
  const res = await fetch(url.toString(), {
    ...init,
    credentials: 'include',
    headers,
  })
  const text = await res.text()
  let data: unknown
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    throw new Error(res.ok ? 'Invalid JSON' : text || res.statusText)
  }
  if (!res.ok) {
    const err = data as { message?: string; code?: string; [k: string]: unknown }
    const msg = err?.message || (typeof err === 'string' ? err : res.statusText)
    const e = new Error(msg) as Error & { code?: string }
    e.code = err?.code
    throw e
  }
  return data as T
}

export const get = <T>(path: string, params?: Record<string, string>) =>
  api<T>(path, { method: 'GET', params })
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined })
export const put = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined })
export const del = <T>(path: string) => api<T>(path, { method: 'DELETE' })

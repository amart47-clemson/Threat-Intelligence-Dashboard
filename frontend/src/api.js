// Prefer explicit API URL in production (Render). Fallback: same-origin /api rewrite.
const API_BASE = (import.meta.env.VITE_API_URL || '').trim().replace(/\/$/, '');

async function request(path, options = {}, retries = 2) {
  let lastError;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const res = await fetch(`${API_BASE}${path}`, options);
      const contentType = res.headers.get('content-type') || '';

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || `Request failed (${res.status})`);
      }

      if (!contentType.includes('application/json')) {
        const text = await res.text();
        throw new Error(
          text.includes('<!DOCTYPE')
            ? 'API returned HTML instead of JSON — check VITE_API_URL or Render rewrite'
            : 'API returned non-JSON response'
        );
      }

      const data = await res.json();
      return data;
    } catch (err) {
      lastError = err;
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 800 * (attempt + 1)));
      }
    }
  }
  throw lastError;
}

export function fetchIOCs({
  type,
  severity,
  country,
  search,
  sort,
  hasCoords,
  page = 1,
  limit = 25,
} = {}) {
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  if (severity) params.set('severity', severity);
  if (country) params.set('country', country);
  if (search) params.set('search', search);
  if (sort) params.set('sort', sort);
  if (hasCoords) params.set('has_coords', 'true');
  params.set('page', String(page));
  params.set('limit', String(limit));
  return request(`/api/iocs?${params}`).then((data) => {
    if (!Array.isArray(data?.iocs)) {
      throw new Error('Invalid IOC list response from API');
    }
    return data;
  });
}

export function fetchIOC(id) {
  return request(`/api/iocs/${id}`);
}

export function fetchStats() {
  return request('/api/stats');
}

export function fetchFeedStatus() {
  return request('/api/feed-status');
}

export function runFeed(feed) {
  return request('/api/feed/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ feed }),
  });
}

export function lookupIOC(value) {
  return request(`/api/lookup?q=${encodeURIComponent(value)}`);
}

export function getExportUrl() {
  return `${API_BASE}/api/export?format=csv`;
}

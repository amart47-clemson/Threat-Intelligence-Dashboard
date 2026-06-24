const API_BASE = import.meta.env.VITE_API_URL || '';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || 'Request failed');
  }
  return res.json();
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
  params.set('page', page);
  params.set('limit', limit);
  return request(`/api/iocs?${params}`);
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

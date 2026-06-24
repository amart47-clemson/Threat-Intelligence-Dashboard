const SEVERITY_COLORS = {
  Low: '#00ff88',
  Medium: '#ffcc00',
  High: '#ff6b35',
  Critical: '#ff2d55',
};

const MARKER_RADIUS = {
  Low: 8,
  Medium: 10,
  High: 12,
  Critical: 14,
};

const regionNames = new Intl.DisplayNames(['en'], { type: 'region' });

export function severityColor(severity) {
  return SEVERITY_COLORS[severity] || '#6b8fa8';
}

export function markerRadius(severity) {
  return MARKER_RADIUS[severity] || 10;
}

export function severityStyles(severity) {
  const color = severityColor(severity);
  return {
    borderColor: color,
    color,
    backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
  };
}

export function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

export function countryName(code) {
  if (!code || code === '—') return '';
  try {
    return regionNames.of(code.toUpperCase());
  } catch {
    return code;
  }
}

export function flagUrl(code) {
  if (!code || code === '—') return null;
  return `https://flagcdn.com/16x12/${code.toLowerCase()}.png`;
}

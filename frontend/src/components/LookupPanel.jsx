import { useState } from 'react';
import { lookupIOC } from '../api';
import { severityColor, severityStyles, formatDate } from '../utils';
import './LookupPanel.css';

export default function LookupPanel({ onResult }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await lookupIOC(query.trim());
      setResult(data);
      if (onResult) onResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resultColor = result ? severityColor(result.severity) : null;

  return (
    <>
      <button
        className="lookup-trigger font-mono"
        onClick={() => setOpen(!open)}
      >
        <span className="lookup-trigger-text">
          {open ? '// CLOSE' : '// IOC LOOKUP'}
        </span>
        <span className="lookup-scan-line" aria-hidden="true" />
      </button>

      {open && (
        <div className="lookup-panel">
          <h3 className="font-mono section-title">// MANUAL LOOKUP</h3>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              className="font-mono"
              placeholder="IP, domain, or URL..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" className="font-mono" disabled={loading}>
              {loading ? 'SCANNING...' : 'SCAN'}
            </button>
          </form>

          {error && <div className="lookup-error">{error}</div>}

          {result && (
            <div
              className="lookup-result"
              style={{
                borderColor: resultColor,
                boxShadow: `0 0 16px ${resultColor}33`,
              }}
            >
              <div className="result-header">
                <span className="source-badge font-mono" data-source={result.source}>
                  {result.source}
                </span>
                <span
                  className="severity-badge font-mono"
                  style={severityStyles(result.severity)}
                >
                  {result.severity}
                </span>
              </div>
              <p className="result-value font-mono">{result.value}</p>
              <div className="result-grid">
                <div><label>Type</label><span className="font-mono">{result.ioc_type}</span></div>
                <div><label>Score</label><span className="font-mono">{result.threat_score?.toFixed(1)}</span></div>
                <div><label>Country</label><span>{result.country || '—'}</span></div>
                <div><label>Feeds</label><span className="font-mono">{result.feed_count}</span></div>
              </div>
              {result.tags?.length > 0 && (
                <div className="result-tags">
                  {result.tags.map((t) => <span key={t} className="tag font-mono">{t}</span>)}
                </div>
              )}
              <p className="result-meta font-mono">
                LAST SEEN: {formatDate(result.last_seen)}
              </p>
            </div>
          )}
        </div>
      )}
    </>
  );
}

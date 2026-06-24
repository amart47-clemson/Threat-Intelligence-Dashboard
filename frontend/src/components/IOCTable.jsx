import { useState, useEffect, useCallback, Fragment, useRef } from 'react';
import { fetchIOCs, fetchIOC } from '../api';
import { severityStyles, formatDate } from '../utils';
import ScoreChart from './ScoreChart';
import ScoreBar from './ScoreBar';
import CountryFlag from './CountryFlag';
import './IOCTable.css';

const TYPES = ['', 'ip', 'domain', 'url', 'hash'];
const SEVERITIES = ['', 'Low', 'Medium', 'High', 'Critical'];

export default function IOCTable({ refreshKey }) {
  const [iocs, setIocs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [type, setType] = useState('');
  const [severity, setSeverity] = useState('');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [animateRows, setAnimateRows] = useState(false);
  const prevRefresh = useRef(refreshKey);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchIOCs({
        type: type || undefined,
        severity: severity || undefined,
        search: debouncedSearch || undefined,
        page,
        limit: 25,
      });
      setIocs(data.iocs);
      setTotal(data.total);
      if (prevRefresh.current !== refreshKey) {
        setAnimateRows(true);
        prevRefresh.current = refreshKey;
        setTimeout(() => setAnimateRows(false), 600);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [type, severity, debouncedSearch, page, refreshKey]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleExpand = async (ioc) => {
    if (expandedId === ioc.id) {
      setExpandedId(null);
      setHistory([]);
      return;
    }
    setExpandedId(ioc.id);
    try {
      const detail = await fetchIOC(ioc.id);
      setHistory(detail.score_history || []);
    } catch {
      setHistory([]);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / 25));

  return (
    <div className="ioc-table-panel">
      <div className="ioc-table-header">
        <h2 className="font-mono section-title">// IOC REGISTER</h2>
        <div className="ioc-filters">
          <input
            type="text"
            className="font-mono"
            placeholder="Search value..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
          <select className="font-mono" value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}>
            {TYPES.map((t) => (
              <option key={t} value={t}>{t || 'ALL TYPES'}</option>
            ))}
          </select>
          <select className="font-mono" value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>{s || 'ALL SEVERITY'}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading ? (
        <div className="loading font-mono">LOADING IOCs...</div>
      ) : (
        <>
          <div className="table-wrap">
            <table className="ioc-table">
              <thead>
                <tr>
                  <th>VALUE</th>
                  <th>TYPE</th>
                  <th>SEVERITY</th>
                  <th>SCORE</th>
                  <th>COUNTRY</th>
                  <th>FEEDS</th>
                  <th>LAST SEEN</th>
                </tr>
              </thead>
              <tbody>
                {iocs.length === 0 ? (
                  <tr><td colSpan={7} className="empty font-mono">NO IOCS FOUND</td></tr>
                ) : iocs.map((ioc, idx) => (
                  <Fragment key={ioc.id}>
                    <tr
                      className={[
                        idx % 2 === 0 ? 'row-even' : 'row-odd',
                        expandedId === ioc.id ? 'expanded-row' : '',
                        animateRows ? 'row-slide-in' : '',
                      ].filter(Boolean).join(' ')}
                      style={{ animationDelay: animateRows ? `${idx * 40}ms` : undefined }}
                      onClick={() => toggleExpand(ioc)}
                    >
                      <td className="value-cell" title={ioc.value}>
                        <span className="value-text font-mono">{ioc.value}</span>
                        <span className="typing-cursor font-mono">|</span>
                      </td>
                      <td className="font-mono">{ioc.ioc_type}</td>
                      <td>
                        <span
                          className="severity-badge font-mono"
                          style={severityStyles(ioc.severity)}
                        >
                          {ioc.severity}
                        </span>
                      </td>
                      <td>
                        <ScoreBar score={ioc.threat_score} severity={ioc.severity} />
                      </td>
                      <td>
                        <CountryFlag code={ioc.country} />
                      </td>
                      <td className="font-mono">{ioc.feed_count}</td>
                      <td className="font-mono">{formatDate(ioc.last_seen)}</td>
                    </tr>
                    {expandedId === ioc.id && (
                      <tr className="chart-row">
                        <td colSpan={7}>
                          <ScoreChart data={history} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination font-mono">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>PREV</button>
            <span>PAGE {page} / {totalPages} ({total} TOTAL)</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>NEXT</button>
          </div>
        </>
      )}
    </div>
  );
}

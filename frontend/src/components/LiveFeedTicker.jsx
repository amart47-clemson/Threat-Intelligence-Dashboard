import { useState, useEffect } from 'react';
import { fetchIOCs } from '../api';
import { severityColor } from '../utils';
import './LiveFeedTicker.css';

function TickerItem({ ioc }) {
  const color = severityColor(ioc.severity);
  return (
    <span className="ticker-item font-mono">
      <span className="ticker-severity" style={{ color }}>[{ioc.severity.toUpperCase()}]</span>
      {' '}
      <span className="ticker-value">{ioc.value}</span>
      {' // '}
      <span>{ioc.ioc_type.toUpperCase()}</span>
      {' // '}
      <span>{ioc.country || 'N/A'}</span>
      <span className="ticker-sep"> ◆ </span>
    </span>
  );
}

export default function LiveFeedTicker() {
  const [iocs, setIocs] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchIOCs({ limit: 20, sort: 'last_seen' });
        setIocs(data.iocs);
      } catch (err) {
        console.error('Ticker fetch failed:', err);
      }
    };
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, []);

  const content = iocs.length > 0
    ? iocs.map((ioc) => <TickerItem key={ioc.id} ioc={ioc} />)
    : <span className="ticker-item font-mono">AWAITING FEED DATA...</span>;

  return (
    <div className="live-feed-ticker">
      <div className="ticker-label font-mono">
        // LIVE FEED<span className="ticker-cursor">|</span>
      </div>
      <div className="ticker-track-wrap">
        <div className="ticker-track font-mono">
          {content}
          {content}
        </div>
      </div>
    </div>
  );
}

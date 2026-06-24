import { useState, useEffect, useCallback } from 'react';
import { fetchStats, fetchIOCs, getExportUrl } from './api';
import { formatDate } from './utils';
import { useCountUp } from './hooks/useCountUp';
import IOCTable from './components/IOCTable';
import ThreatMap from './components/ThreatMap';
import LookupPanel from './components/LookupPanel';
import LiveFeedTicker from './components/LiveFeedTicker';
import TypeDonutChart from './components/TypeDonutChart';
import FeedActivityPanel from './components/FeedActivityPanel';
import './App.css';

function StatIcon({ type }) {
  const icons = {
    shield: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2L4 6v6c0 5.25 3.5 10 8 11 4.5-1 8-5.75 8-11V6l-8-4z" />
      </svg>
    ),
    skull: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="9" cy="10" r="2" />
        <circle cx="15" cy="10" r="2" />
        <path d="M8 14v3M12 14v3M16 14v3M6 18h12M12 2C8 2 5 5 5 9c0 2 1 4 2 5h10c1-1 2-3 2-5 0-4-3-7-7-7z" />
      </svg>
    ),
    warning: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2L2 20h20L12 2z" />
        <path d="M12 9v5M12 17h.01" />
      </svg>
    ),
    globe: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
      </svg>
    ),
  };
  return <span className="stat-icon">{icons[type]}</span>;
}

function StatCard({ label, value, accent, icon, pulse, delayClass }) {
  const numericValue = value ?? 0;
  const displayCount = useCountUp(numericValue);
  const showDash = value == null;

  return (
    <div
      className={`stat-card animate-in ${delayClass} ${pulse ? 'critical-active' : ''}`}
      style={{ '--card-accent': accent }}
    >
      <div className="stat-card-glow" />
      <StatIcon type={icon} />
      <span className="stat-value font-mono">
        {showDash ? '—' : displayCount}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

function BackgroundGrid() {
  return (
    <div className="bg-layer" aria-hidden="true">
      <svg className="bg-grid-svg" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke="#0f2440"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
      <div className="bg-radial" />
    </div>
  );
}

export default function App() {
  const [stats, setStats] = useState(null);
  const [mapIOCs, setMapIOCs] = useState([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadStats = useCallback(async () => {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  }, []);

  const loadMapData = useCallback(async () => {
    try {
      const data = await fetchIOCs({
        type: 'ip',
        hasCoords: true,
        limit: 500,
        page: 1,
      });
      setMapIOCs(data.iocs);
    } catch (err) {
      console.error('Failed to load map data:', err);
    }
  }, []);

  useEffect(() => {
    loadStats();
    loadMapData();
    const interval = setInterval(loadStats, 60000);
    return () => clearInterval(interval);
  }, [loadStats, loadMapData, refreshKey]);

  const handleLookupResult = () => {
    setRefreshKey((k) => k + 1);
    loadMapData();
    loadStats();
  };

  return (
    <div className="app">
      <BackgroundGrid />

      <nav className="top-nav animate-in">
        <div className="nav-sweep" />
        <div className="nav-brand">
          <h1 className="font-mono app-title">THREAT INTEL // DASHBOARD</h1>
          <span className="last-updated font-mono">
            // LAST SYNC: {stats?.last_updated ? formatDate(stats.last_updated) : '—'}
          </span>
        </div>
        <a className="export-btn font-mono" href={getExportUrl()} download>
          EXPORT CSV
        </a>
      </nav>

      <LiveFeedTicker />

      <div className="stat-cards">
        <StatCard
          label="Total IOCs"
          value={stats?.total_iocs}
          accent="#00d4ff"
          icon="shield"
          delayClass="animate-in-delay-1"
        />
        <StatCard
          label="Critical"
          value={stats?.critical_count}
          accent="#ff2d55"
          icon="skull"
          pulse={(stats?.critical_count ?? 0) > 0}
          delayClass="animate-in-delay-2"
        />
        <StatCard
          label="High"
          value={stats?.high_count}
          accent="#ff6b35"
          icon="warning"
          delayClass="animate-in-delay-3"
        />
        <StatCard
          label="Countries"
          value={stats?.countries_count}
          accent="#00ff88"
          icon="globe"
          delayClass="animate-in-delay-4"
        />
        <TypeDonutChart stats={stats} />
      </div>

      <main className="main-layout">
        <div className="map-section animate-in animate-in-delay-4">
          <ThreatMap iocs={mapIOCs} />
        </div>
        <div className="table-section animate-in animate-in-delay-5">
          <IOCTable refreshKey={refreshKey} />
        </div>
      </main>

      <FeedActivityPanel refreshKey={refreshKey} />

      <LookupPanel onResult={handleLookupResult} />
    </div>
  );
}

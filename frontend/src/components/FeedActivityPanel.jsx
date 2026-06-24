import { useState, useEffect, useCallback } from 'react';
import { fetchFeedStatus, runFeed } from '../api';
import { formatDate } from '../utils';
import './FeedActivityPanel.css';

export default function FeedActivityPanel({ refreshKey }) {
  const [feeds, setFeeds] = useState([]);
  const [runningFeeds, setRunningFeeds] = useState({});
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchFeedStatus();
      setFeeds(data.feeds || []);
      const running = {};
      data.feeds?.forEach((f) => { running[f.feed] = f.running; });
      setRunningFeeds(running);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, [load, refreshKey]);

  useEffect(() => {
    if (!Object.values(runningFeeds).some(Boolean)) return undefined;
    const poll = setInterval(load, 2000);
    return () => clearInterval(poll);
  }, [runningFeeds, load]);

  const handleRun = async (feedKey) => {
    setRunningFeeds((prev) => ({ ...prev, [feedKey]: true }));
    try {
      await runFeed(feedKey);
      await load();
    } catch (err) {
      setError(err.message);
      setRunningFeeds((prev) => ({ ...prev, [feedKey]: false }));
    }
  };

  return (
    <div className="feed-activity-panel animate-in animate-in-delay-5">
      <h2 className="font-mono section-title">// FEED ACTIVITY</h2>
      {error && <div className="feed-error">{error}</div>}
      <div className="feed-rows">
        {feeds.map((feed) => (
          <div key={feed.feed} className="feed-row">
            <div className="feed-name font-mono">{feed.name}</div>
            <div className="feed-status">
              <span
                className={`status-dot ${feed.status === 'active' ? 'active' : 'idle'}`}
                title={feed.status}
              />
              <span className="status-text font-mono">
                {feed.running ? 'RUNNING' : feed.status.toUpperCase()}
              </span>
              {feed.running && <span className="feed-spinner" />}
            </div>
            <div className="feed-meta font-mono">
              <span>LAST RUN: {feed.last_run ? formatDate(feed.last_run) : '—'}</span>
              <span>LAST INGESTED: {feed.iocs_ingested_last_run}</span>
              <span>TOTAL: {feed.total_iocs}</span>
            </div>
            <button
              type="button"
              className="feed-run-btn font-mono"
              disabled={feed.running || runningFeeds[feed.feed]}
              onClick={() => handleRun(feed.feed)}
            >
              // RUN NOW
            </button>
          </div>
        ))}
        {feeds.length === 0 && (
          <div className="feed-empty font-mono">NO FEED DATA</div>
        )}
      </div>
    </div>
  );
}

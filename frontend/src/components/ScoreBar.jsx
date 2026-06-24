import { severityColor } from '../utils';
import './ScoreBar.css';

export default function ScoreBar({ score, severity }) {
  const color = severityColor(severity);
  const pct = Math.min(100, Math.max(0, score));

  return (
    <div className="score-bar-cell">
      <span className="score-bar-value font-mono" style={{ color }}>
        {score.toFixed(1)}
      </span>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{
            '--bar-color': color,
            '--bar-width': `${pct}%`,
          }}
        />
      </div>
    </div>
  );
}

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { formatDate } from '../utils';

export default function ScoreChart({ data = [] }) {
  if (!data.length) {
    return <p className="no-history">NO SCORE HISTORY AVAILABLE</p>;
  }

  const chartData = data.map((d) => ({
    ...d,
    label: formatDate(d.recorded_at),
  }));

  return (
    <div className="score-chart">
      <h4>// SCORE HISTORY</h4>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={chartData} margin={{ top: 8, right: 20, bottom: 5, left: 0 }}>
          <defs>
            <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00d4ff" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#00d4ff" stopOpacity={0} />
            </linearGradient>
            <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#0f2440" />
          <XAxis
            dataKey="label"
            tick={{ fill: '#6b8fa8', fontSize: 9, fontFamily: 'Share Tech Mono' }}
            interval="preserveStartEnd"
            axisLine={{ stroke: '#0f2440' }}
            tickLine={{ stroke: '#0f2440' }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: '#6b8fa8', fontSize: 9, fontFamily: 'Share Tech Mono' }}
            axisLine={{ stroke: '#0f2440' }}
            tickLine={{ stroke: '#0f2440' }}
          />
          <Tooltip
            contentStyle={{
              background: '#0d1224',
              border: '1px solid #1e3a5f',
              fontFamily: 'Share Tech Mono',
              fontSize: '0.75rem',
            }}
            labelStyle={{ color: '#e8f4fd' }}
            itemStyle={{ color: '#00d4ff' }}
          />
          <Area
            type="monotone"
            dataKey="threat_score"
            stroke="#00d4ff"
            strokeWidth={2}
            fill="url(#scoreGradient)"
            dot={{ fill: '#00d4ff', r: 3, strokeWidth: 0 }}
            activeDot={{ r: 5, fill: '#00d4ff', stroke: '#00d4ff', strokeWidth: 2 }}
            filter="url(#lineGlow)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

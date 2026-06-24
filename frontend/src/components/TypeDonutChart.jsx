import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import './TypeDonutChart.css';

const TYPE_COLORS = {
  ip: '#00d4ff',
  domain: '#7b2fff',
  url: '#ff6b35',
};

export default function TypeDonutChart({ stats }) {
  const data = [
    { name: 'IP', key: 'ip', value: stats?.ip_count ?? 0 },
    { name: 'Domain', key: 'domain', value: stats?.domain_count ?? 0 },
    { name: 'URL', key: 'url', value: stats?.url_count ?? 0 },
  ].filter((d) => d.value > 0);

  const total = stats?.total_iocs ?? 0;
  const hasData = data.length > 0;

  return (
    <div className="type-donut-card animate-in animate-in-delay-5">
      <h3 className="font-mono section-title">// IOC TYPES</h3>
      <div className="donut-wrap">
        <ResponsiveContainer width="100%" height={140}>
          <PieChart>
            <Pie
              data={hasData ? data : [{ name: 'Empty', value: 1 }]}
              cx="50%"
              cy="50%"
              innerRadius={42}
              outerRadius={58}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {hasData ? (
                data.map((entry) => (
                  <Cell key={entry.key} fill={TYPE_COLORS[entry.key]} />
                ))
              ) : (
                <Cell fill="#0f2440" />
              )}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-center font-mono">{total}</div>
      </div>
      <div className="donut-legend">
        {['ip', 'domain', 'url'].map((key) => (
          <span key={key} className="legend-item">
            <span className="legend-dot" style={{ background: TYPE_COLORS[key] }} />
            <span className="font-mono">{key.toUpperCase()}</span>
            <span className="legend-count font-mono">{stats?.[`${key}_count`] ?? 0}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

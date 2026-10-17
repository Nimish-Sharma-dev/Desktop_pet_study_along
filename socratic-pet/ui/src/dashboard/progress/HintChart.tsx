import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';

export function HintChart() {
  const data = useStore((s) => s.progress?.hint_dependency) ?? [];
  const half = Math.floor(data.length / 2);
  const avg = (xs: typeof data) => (xs.length ? xs.reduce((a, b) => a + b.avg_hint_level, 0) / xs.length : 0);
  const before = avg(data.slice(0, half)), after = avg(data.slice(half));
  const change = before > 0 ? Math.round(((after - before) / before) * 100) : 0;

  return (
    <GlassCard
      title="Hint dependency"
      right={data.length > 3 && (
        <span className="text-[11px]" style={{ color: change <= 0 ? '#4ade80' : '#ff6b81' }}>
          {change <= 0 ? '↓' : '↑'} {Math.abs(change)}% vs earlier
        </span>
      )}
    >
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="hintFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--d-accent)" stopOpacity={0.45} />
              <stop offset="100%" stopColor="var(--d-accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--d-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} tick={{ fill: 'var(--d-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 4]} ticks={[0, 1, 2, 3, 4]} tick={{ fill: 'var(--d-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: 'rgba(14,16,28,0.92)', border: '1px solid var(--d-border)', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: 'var(--d-muted)' }}
            formatter={(v) => [String(v), 'avg hint level']}
          />
          <Area type="monotone" dataKey="avg_hint_level" stroke="var(--d-accent)" strokeWidth={2} fill="url(#hintFill)" />
        </AreaChart>
      </ResponsiveContainer>
      <p className="mt-1 text-[10px]" style={{ color: 'var(--d-muted)' }}>Average hint level needed per day (0 to 4). Lower means more independent.</p>
    </GlassCard>
  );
}

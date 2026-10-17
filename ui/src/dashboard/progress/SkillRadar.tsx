import { useEffect, useState } from 'react';
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from 'recharts';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { humanize } from '../util';

export function SkillRadar() {
  const radar = useStore((s) => s.progress?.skill_radar);
  const mode = useStore((s) => s.mode);
  const [track, setTrack] = useState<string>(mode);
  useEffect(() => setTrack(mode), [mode]);

  const tracks = Object.keys(radar ?? {});
  const data = radar?.[track] ?? radar?.[tracks[0]] ?? [];

  return (
    <GlassCard
      title="Skill radar"
      right={
        <div className="flex gap-1">
          {tracks.map((t) => (
            <button
              key={t}
              onClick={() => setTrack(t)}
              className="rounded-full border px-2 py-0.5 text-[10px]"
              style={{ borderColor: t === track ? 'var(--d-accent)' : 'var(--d-border)', color: t === track ? 'var(--d-accent)' : 'var(--d-muted)' }}
            >{humanize(t)}</button>
          ))}
        </div>
      }
    >
      <ResponsiveContainer width="100%" height={250}>
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="var(--d-border)" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: 'var(--d-muted)', fontSize: 11 }} />
          <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
          <Radar dataKey="value" stroke="var(--d-accent)" fill="var(--d-accent)" fillOpacity={0.3} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </GlassCard>
  );
}

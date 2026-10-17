const CELL = 12;
const GAP = 3;
const LEVEL_PCT = [0, 28, 48, 72, 100];
const level = (c: number) => (c === 0 ? 0 : c < 4 ? 1 : c < 8 ? 2 : c < 12 ? 3 : 4);
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

type Day = { date: string; count: number };

export function Heatmap({ data }: { data: Day[] }) {
  if (!data.length) return <p className="text-xs" style={{ color: 'var(--d-muted)' }}>No activity yet.</p>;
  const pad = new Date(data[0].date + 'T00:00:00').getDay(); // weeks start on Sunday
  const cells: (Day | null)[] = [...Array<null>(pad).fill(null), ...data];
  const weeks: (Day | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

  const left = 22, top = 16;
  const width = left + weeks.length * (CELL + GAP);
  const height = top + 7 * (CELL + GAP);

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} role="img" aria-label="Daily activity heatmap">
        {[1, 3, 5].map((d) => (
          <text key={d} x={0} y={top + d * (CELL + GAP) + CELL - 2} fontSize="9" fill="var(--d-muted)">{'SMTWTFS'[d]}</text>
        ))}
        {weeks.map((w, wi) => {
          const first = w.find((c) => c);
          const showMonth = first && Number(first.date.slice(8, 10)) <= 7;
          return (
            <g key={wi} transform={`translate(${left + wi * (CELL + GAP)},0)`}>
              {showMonth && first && <text x={0} y={10} fontSize="9" fill="var(--d-muted)">{MONTHS[Number(first.date.slice(5, 7)) - 1]}</text>}
              {w.map((c, di) => c && (
                <rect
                  key={di}
                  x={0}
                  y={top + di * (CELL + GAP)}
                  width={CELL}
                  height={CELL}
                  rx={3}
                  style={{ fill: level(c.count) === 0 ? 'rgba(255,255,255,0.06)' : `color-mix(in srgb, var(--d-accent) ${LEVEL_PCT[level(c.count)]}%, transparent)` }}
                >
                  <title>{`${c.date}: ${c.count} attempt${c.count === 1 ? '' : 's'}`}</title>
                </rect>
              ))}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';

const COLORS = ['#7c9cff', '#b388ff', '#4ade80', '#ffd666', '#ff6b81', '#7fd4ff'];

// Canvas overlay for the whole pet window, never part of the hit rects (always click-through).
export function Confetti() {
  const tick = useStore((s) => s.confetti.tick);
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!tick || !canvas) return;
    const count = Math.min(useStore.getState().confetti.count || 120, 300);
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const ps = Array.from({ length: count }, () => ({
      x: w / 2, y: h - 110,
      vx: (Math.random() - 0.5) * 11, vy: -(7 + Math.random() * 10),
      size: 5 + Math.random() * 6, rot: Math.random() * 6.28, vr: (Math.random() - 0.5) * 0.4,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      life: 0, ttl: 90 + Math.random() * 70,
    }));

    let raf = 0;
    const step = () => {
      ctx.clearRect(0, 0, w, h);
      let alive = false;
      for (const p of ps) {
        if (p.life++ > p.ttl) continue;
        alive = true;
        p.vy += 0.28; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.rot += p.vr;
        ctx.save();
        ctx.globalAlpha = Math.max(0, 1 - p.life / p.ttl);
        ctx.translate(p.x, p.y); ctx.rotate(p.rot);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 3, p.size, p.size * 0.6);
        ctx.restore();
      }
      if (alive) raf = requestAnimationFrame(step); else ctx.clearRect(0, 0, w, h);
    };
    step();
    return () => cancelAnimationFrame(raf);
  }, [tick]);

  return <canvas ref={ref} className="pointer-events-none absolute inset-0 h-full w-full" />;
}

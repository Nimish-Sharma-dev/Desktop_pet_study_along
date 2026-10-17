import { useEffect } from 'react';
import { invoke, isTauri } from '../lib/tauri';

const PAD = 4; // px of grace around every interactive element

// Reports the rectangles of every [data-hit] element to Rust. Everything outside them is
// click-through. Polled (not observer-driven) because CSS transforms/animations move
// elements without firing resize events; unchanged reports are deduplicated.
export function useHitRects() {
  useEffect(() => {
    if (!isTauri) return;
    let last = '';
    const report = () => {
      const rects = [...document.querySelectorAll<HTMLElement>('[data-hit]')].map((el) => {
        const r = el.getBoundingClientRect();
        return { x: r.left - PAD, y: r.top - PAD, w: r.width + PAD * 2, h: r.height + PAD * 2 };
      });
      const key = JSON.stringify(rects.map((r) => [r.x, r.y, r.w, r.h].map(Math.round)));
      if (key === last) return;
      last = key;
      void invoke('set_hit_rects', { rects });
    };
    report();
    const id = window.setInterval(report, 120);
    window.addEventListener('resize', report);
    return () => { window.clearInterval(id); window.removeEventListener('resize', report); };
  }, []);
}

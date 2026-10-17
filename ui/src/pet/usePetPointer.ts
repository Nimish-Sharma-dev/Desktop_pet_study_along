import { useEffect, useRef } from 'react';
import { startDragging } from '../lib/tauri';

const DRAG_THRESHOLD = 4; // px of movement before a press becomes a drag

// Press + move > threshold = drag the window. Press + release = click.
export function usePetPointer(onClick: () => void) {
  const down = useRef<{ x: number; y: number } | null>(null);
  const clickRef = useRef(onClick);
  clickRef.current = onClick;

  useEffect(() => {
    const move = (e: MouseEvent) => {
      const d = down.current;
      if (!d) return;
      if (Math.hypot(e.clientX - d.x, e.clientY - d.y) > DRAG_THRESHOLD) {
        down.current = null;
        void startDragging();
      }
    };
    const up = () => {
      if (!down.current) return;
      down.current = null;
      clickRef.current();
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
    return () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up); };
  }, []);

  return {
    onMouseDown: (e: React.MouseEvent) => {
      if (e.button === 0) down.current = { x: e.clientX, y: e.clientY };
    },
  };
}

import { api } from './rest';
import { parseUiMessage, setIssueSink } from './normalize';
import { connectUiSocket } from './ws';
import { useStore } from '../store/useStore';
import type { UiMessage } from '../types/contracts';

// Wires /ws/ui -> store. Messages are queued and flushed once per frame
// (with a timer fallback for hidden windows) so bursts never cause render storms.
let started = false;

export function startUiFeed() {
  if (started) return;
  started = true;
  const store = useStore.getState();
  setIssueSink(store.reportIssues);

  let queue: UiMessage[] = [];
  let scheduled = false;
  const flush = () => {
    if (!scheduled) return;
    scheduled = false;
    const batch = queue;
    queue = [];
    if (batch.length) {
      useStore.getState().applyBatch(batch);
      // keep streak / timeline / mistakes fresh: refetch progress shortly after activity
      if (batch.some((m) => ['bubble', 'confetti', 'mastery_update', 'review'].includes(m.channel))) refreshProgress();
    }
  };
  let refreshTimer: ReturnType<typeof setTimeout> | undefined;
  const refreshProgress = () => {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => api.progress().then(store.setProgress).catch(() => {}), 900);
  };
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(flush);
    setTimeout(flush, 100);
  };

  // slow safety net: pick up changes that no event announces (e.g. spaced-repetition items becoming due)
  setInterval(() => { if (useStore.getState().connected) api.progress().then(store.setProgress).catch(() => {}); }, 60_000);

  connectUiSocket(
    (raw) => { const m = parseUiMessage(raw); if (m) { queue.push(m); schedule(); } },
    (connected) => {
      store.setConnected(connected);
      if (connected) {
        // (re)hydrate from REST on every (re)connect
        api.progress().then(store.setProgress).catch(() => {});
        api.graph().then(store.setGraph).catch(() => {});
        api.review().then((r) => { if (r) store.setReview(r); }).catch(() => {});
      }
    },
  );
}

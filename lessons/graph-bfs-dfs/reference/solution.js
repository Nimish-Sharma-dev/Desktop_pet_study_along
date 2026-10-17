function adjacency(n, edges) {
  const adj = Array.from({ length: n }, () => []);
  for (const [u, v] of edges) {
    adj[u].push(v);
    adj[v].push(u);
  }
  return adj;
}

function shortestPath(n, edges, src, dst) {
  const adj = adjacency(n, edges);
  const dist = new Map([[src, 0]]);
  const queue = [src];
  let head = 0;
  while (head < queue.length) {
    const node = queue[head++];
    if (node === dst) return dist.get(node);
    for (const nb of adj[node]) {
      if (!dist.has(nb)) {
        dist.set(nb, dist.get(node) + 1);
        queue.push(nb);
      }
    }
  }
  return -1;
}

function countComponents(n, edges) {
  const adj = adjacency(n, edges);
  const seen = new Array(n).fill(false);
  let count = 0;
  for (let start = 0; start < n; start++) {
    if (seen[start]) continue;
    count++;
    seen[start] = true;
    const stack = [start];
    while (stack.length > 0) {
      const node = stack.pop();
      for (const nb of adj[node]) {
        if (!seen[nb]) {
          seen[nb] = true;
          stack.push(nb);
        }
      }
    }
  }
  return count;
}

module.exports = { shortestPath, countComponents };

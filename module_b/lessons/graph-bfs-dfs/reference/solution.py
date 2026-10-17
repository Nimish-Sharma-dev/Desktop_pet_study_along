from collections import deque


def _adjacency(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def shortest_path(n, edges, src, dst):
    adj = _adjacency(n, edges)
    dist = {src: 0}
    queue = deque([src])
    while queue:
        node = queue.popleft()
        if node == dst:
            return dist[node]
        for nb in adj[node]:
            if nb not in dist:
                dist[nb] = dist[node] + 1
                queue.append(nb)
    return -1


def count_components(n, edges):
    adj = _adjacency(n, edges)
    seen = [False] * n
    count = 0
    for start in range(n):
        if seen[start]:
            continue
        count += 1
        seen[start] = True
        stack = [start]
        while stack:
            node = stack.pop()
            for nb in adj[node]:
                if not seen[nb]:
                    seen[nb] = True
                    stack.append(nb)
    return count

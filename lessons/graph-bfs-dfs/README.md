# Graphs: BFS and DFS

Two functions on an undirected graph (nodes `0..n-1`, edges as `[u, v]` pairs):

* `shortest_path(n, edges, src, dst)` - fewest edges between two nodes, `-1` if they are not connected.
* `count_components(n, edges)` - number of connected components.

Think about: cycles, nodes with no edges, and a graph that is one very long chain.

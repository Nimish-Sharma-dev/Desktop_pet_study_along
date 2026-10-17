package solution

func adjacency(n int, edges [][]int) [][]int {
	adj := make([][]int, n)
	for _, e := range edges {
		adj[e[0]] = append(adj[e[0]], e[1])
		adj[e[1]] = append(adj[e[1]], e[0])
	}
	return adj
}

func ShortestPath(n int, edges [][]int, src int, dst int) int {
	adj := adjacency(n, edges)
	dist := map[int]int{src: 0}
	queue := []int{src}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		if node == dst {
			return dist[node]
		}
		for _, nb := range adj[node] {
			if _, ok := dist[nb]; !ok {
				dist[nb] = dist[node] + 1
				queue = append(queue, nb)
			}
		}
	}
	return -1
}

func CountComponents(n int, edges [][]int) int {
	adj := adjacency(n, edges)
	seen := make([]bool, n)
	count := 0
	for start := 0; start < n; start++ {
		if seen[start] {
			continue
		}
		count++
		seen[start] = true
		stack := []int{start}
		for len(stack) > 0 {
			node := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			for _, nb := range adj[node] {
				if !seen[nb] {
					seen[nb] = true
					stack = append(stack, nb)
				}
			}
		}
	}
	return count
}

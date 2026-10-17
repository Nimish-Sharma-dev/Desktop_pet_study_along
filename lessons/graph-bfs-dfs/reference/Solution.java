import java.util.*;

public class Solution {
    private static List<List<Integer>> adjacency(int n, int[][] edges) {
        List<List<Integer>> adj = new ArrayList<>();
        for (int i = 0; i < n; i++) adj.add(new ArrayList<>());
        for (int[] e : edges) {
            adj.get(e[0]).add(e[1]);
            adj.get(e[1]).add(e[0]);
        }
        return adj;
    }

    public static int shortestPath(int n, int[][] edges, int src, int dst) {
        List<List<Integer>> adj = adjacency(n, edges);
        Map<Integer, Integer> dist = new HashMap<>();
        dist.put(src, 0);
        Deque<Integer> queue = new ArrayDeque<>();
        queue.add(src);
        while (!queue.isEmpty()) {
            int node = queue.poll();
            if (node == dst) return dist.get(node);
            for (int nb : adj.get(node)) {
                if (!dist.containsKey(nb)) {
                    dist.put(nb, dist.get(node) + 1);
                    queue.add(nb);
                }
            }
        }
        return -1;
    }

    public static int countComponents(int n, int[][] edges) {
        List<List<Integer>> adj = adjacency(n, edges);
        boolean[] seen = new boolean[n];
        int count = 0;
        for (int start = 0; start < n; start++) {
            if (seen[start]) continue;
            count++;
            seen[start] = true;
            Deque<Integer> stack = new ArrayDeque<>();
            stack.push(start);
            while (!stack.isEmpty()) {
                int node = stack.pop();
                for (int nb : adj.get(node)) {
                    if (!seen[nb]) {
                        seen[nb] = true;
                        stack.push(nb);
                    }
                }
            }
        }
        return count;
    }
}

public class ListKit {
    public static Solution.ListNode fromList(int[] a) {
        Solution.ListNode head = null;
        for (int i = a.length - 1; i >= 0; i--) head = new Solution.ListNode(a[i], head);
        return head;
    }

    public static int[] toList(Solution.ListNode h) {
        java.util.ArrayList<Integer> out = new java.util.ArrayList<>();
        int n = 0;
        while (h != null) {
            if (++n > 1000000) throw new IllegalStateException("returned list has a cycle");
            out.add(h.val);
            h = h.next;
        }
        return out.stream().mapToInt(Integer::intValue).toArray();
    }
}

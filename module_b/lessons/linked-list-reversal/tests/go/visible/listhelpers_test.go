package solution

func fromList(a []int) *ListNode {
	var head *ListNode
	for i := len(a) - 1; i >= 0; i-- {
		head = &ListNode{Val: a[i], Next: head}
	}
	return head
}

func toList(h *ListNode) []int {
	out := []int{}
	for n := 0; h != nil; n++ {
		if n > 1000000 {
			panic("returned list has a cycle")
		}
		out = append(out, h.Val)
		h = h.Next
	}
	return out
}

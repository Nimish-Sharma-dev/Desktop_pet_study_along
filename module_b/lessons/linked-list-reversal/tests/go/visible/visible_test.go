package solution

import "testing"

func Test_five_nodes(t *testing.T) {
	runCase(t, func() interface{} { return toList(ReverseList(fromList([]int{1,2,3,4,5}))) }, []int{5,4,3,2,1})
}

func Test_two_nodes(t *testing.T) {
	runCase(t, func() interface{} { return toList(ReverseList(fromList([]int{1,2}))) }, []int{2,1})
}


package solution

import "testing"

func Test_basic(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{2,7,11,15}, 9) }, []int{0,1})
}

func Test_middle_pair(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{1,2,4,6,10}, 8) }, []int{1,3})
}

func Test_outer_pair(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{1,3,4,8}, 9) }, []int{0,3})
}

func Test_no_pair(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{1,2,3}, 10) }, []int{})
}


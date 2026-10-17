package solution

import "testing"

func Test_hidden_empty(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{}, 5) }, []int{})
}

func Test_hidden_single_cannot_pair_with_itself(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{5}, 10) }, []int{})
}

func Test_hidden_duplicates(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{1,1,3,5}, 2) }, []int{0,1})
}

func Test_hidden_negatives(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted([]int{-4,-1,0,3,10}, -5) }, []int{0,1})
}

func Test_hidden_large(t *testing.T) {
	runCase(t, func() interface{} { return TwoSumSorted(lessonRange(0, 300000, 2), 1199994) }, []int{299998,299999})
}


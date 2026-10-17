package solution

import "testing"

func Test_hidden_empty(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{}, 3) }, -1)
}

func Test_hidden_single_found(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{4}, 4) }, 0)
}

func Test_hidden_single_missing(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{4}, 7) }, -1)
}

func Test_hidden_two_elements(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{1,3}, 3) }, 1)
}

func Test_hidden_below_min(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{5,6,7}, 1) }, -1)
}

func Test_hidden_large(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch(lessonRange(0, 1000000, 1), 999999) }, 999999)
}


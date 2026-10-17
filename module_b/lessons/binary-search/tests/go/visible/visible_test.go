package solution

import "testing"

func Test_found_middle(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{1,3,5,7,9}, 5) }, 2)
}

func Test_found_first(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{1,3,5,7,9}, 1) }, 0)
}

func Test_found_last(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{1,3,5,7,9}, 9) }, 4)
}

func Test_not_found_inside(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{1,3,5,7,9}, 4) }, -1)
}

func Test_not_found_above(t *testing.T) {
	runCase(t, func() interface{} { return BinarySearch([]int{1,3,5,7,9}, 10) }, -1)
}


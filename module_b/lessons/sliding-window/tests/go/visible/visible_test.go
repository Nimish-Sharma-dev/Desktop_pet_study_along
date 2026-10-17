package solution

import "testing"

func Test_basic(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{1,4,2,10,2,3,1,0,20}, 4) }, 24)
}

func Test_small_window(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{2,1,5,1,3,2}, 3) }, 9)
}

func Test_one_element(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{5}, 1) }, 5)
}

func Test_all_negative(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{-3,-1,-2}, 2) }, -3)
}


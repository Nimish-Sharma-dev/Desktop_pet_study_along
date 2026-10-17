package solution

import "testing"

func Test_hidden_window_is_whole_list(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{1,2,3}, 3) }, 6)
}

func Test_hidden_window_too_big(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{1,2}, 5) }, 0)
}

func Test_hidden_empty(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{}, 3) }, 0)
}

func Test_hidden_zero_window(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum([]int{1,2,3}, 0) }, 0)
}

func Test_hidden_large(t *testing.T) {
	runCase(t, func() interface{} { return MaxWindowSum(lessonRange(0, 1500000, 1), 5000) }, 7487497500)
}


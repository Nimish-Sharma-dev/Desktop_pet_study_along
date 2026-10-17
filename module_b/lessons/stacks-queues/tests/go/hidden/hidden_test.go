package solution

import "testing"

func Test_hidden_empty_string(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("") }, true)
}

func Test_hidden_only_open(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("((") }, false)
}

func Test_hidden_close_first(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses(")(") }, false)
}

func Test_hidden_only_close(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("]") }, false)
}

func Test_hidden_unclosed_after_valid(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("()[") }, false)
}

func Test_hidden_temps_empty(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{}) }, []int{})
}

func Test_hidden_temps_single(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{5}) }, []int{0})
}

func Test_hidden_temps_falling(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{5,4,3}) }, []int{0,0,0})
}

func Test_hidden_temps_equal(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{5,5,5}) }, []int{0,0,0})
}


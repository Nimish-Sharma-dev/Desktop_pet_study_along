package solution

import "testing"

func Test_valid_simple(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("()") }, true)
}

func Test_valid_mixed(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("()[]{}") }, true)
}

func Test_valid_nested(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("{[]}") }, true)
}

func Test_invalid_wrong_type(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("(]") }, false)
}

func Test_invalid_interleaved(t *testing.T) {
	runCase(t, func() interface{} { return IsValidParentheses("([)]") }, false)
}

func Test_temps_example(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{73,74,75,71,69,72,76,73}) }, []int{1,1,4,2,1,1,0,0})
}

func Test_temps_rising(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{30,40,50,60}) }, []int{1,1,1,0})
}

func Test_temps_short(t *testing.T) {
	runCase(t, func() interface{} { return DailyTemperatures([]int{30,60,90}) }, []int{1,1,0})
}


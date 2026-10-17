package solution

import "testing"

func Test_sum_basic(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{2,7,11,15}, 9) }, []int{0,1})
}

func Test_sum_not_first(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{3,2,4}, 6) }, []int{1,2})
}

func Test_sum_duplicates(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{3,3}, 6) }, []int{0,1})
}

func Test_sum_none(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{1,2,3}, 7) }, []int{})
}

func Test_anagram_yes(t *testing.T) {
	runCase(t, func() interface{} { return IsAnagram("listen", "silent") }, true)
}

func Test_anagram_no(t *testing.T) {
	runCase(t, func() interface{} { return IsAnagram("rat", "car") }, false)
}


package solution

import "testing"

func Test_hidden_sum_empty(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{}, 4) }, []int{})
}

func Test_hidden_sum_no_self_reuse(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{5}, 10) }, []int{})
}

func Test_hidden_sum_negatives(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum([]int{-3,4,3,90}, 0) }, []int{0,2})
}

func Test_hidden_sum_large(t *testing.T) {
	runCase(t, func() interface{} { return TwoSum(lessonRange(0, 300000, 1), 599997) }, []int{299998,299999})
}

func Test_hidden_anagram_empty(t *testing.T) {
	runCase(t, func() interface{} { return IsAnagram("", "") }, true)
}

func Test_hidden_anagram_length_differs(t *testing.T) {
	runCase(t, func() interface{} { return IsAnagram("a", "ab") }, false)
}

func Test_hidden_anagram_same_letters_different_counts(t *testing.T) {
	runCase(t, func() interface{} { return IsAnagram("aacc", "ccac") }, false)
}


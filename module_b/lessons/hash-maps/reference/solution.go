package solution

func TwoSum(nums []int, target int) []int {
	seen := map[int]int{}
	for i, x := range nums {
		if j, ok := seen[target-x]; ok {
			return []int{j, i}
		}
		seen[x] = i
	}
	return []int{}
}

func IsAnagram(s string, t string) bool {
	if len(s) != len(t) {
		return false
	}
	counts := map[rune]int{}
	for _, ch := range s {
		counts[ch]++
	}
	for _, ch := range t {
		if counts[ch] == 0 {
			return false
		}
		counts[ch]--
	}
	return true
}

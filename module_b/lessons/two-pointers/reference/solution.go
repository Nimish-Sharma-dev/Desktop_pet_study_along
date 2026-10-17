package solution

func TwoSumSorted(nums []int, target int) []int {
	left := 0
	right := len(nums) - 1
	for left < right {
		total := nums[left] + nums[right]
		if total == target {
			return []int{left, right}
		}
		if total < target {
			left++
		} else {
			right--
		}
	}
	return []int{}
}

package solution

func MaxWindowSum(nums []int, k int) int {
	if k <= 0 || k > len(nums) {
		return 0
	}
	window := 0
	for i := 0; i < k; i++ {
		window += nums[i]
	}
	best := window
	for i := k; i < len(nums); i++ {
		window += nums[i] - nums[i-k]
		if window > best {
			best = window
		}
	}
	return best
}

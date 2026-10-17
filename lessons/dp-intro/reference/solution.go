package solution

func ClimbStairs(n int) int {
	a := 1
	b := 1
	for i := 0; i < n; i++ {
		a, b = b, a+b
	}
	return a
}

func MinCoins(coins []int, amount int) int {
	inf := amount + 1
	dp := make([]int, amount+1)
	for i := 1; i <= amount; i++ {
		dp[i] = inf
	}
	for a := 1; a <= amount; a++ {
		for _, c := range coins {
			if c <= a && dp[a-c]+1 < dp[a] {
				dp[a] = dp[a-c] + 1
			}
		}
	}
	if dp[amount] != inf {
		return dp[amount]
	}
	return -1
}

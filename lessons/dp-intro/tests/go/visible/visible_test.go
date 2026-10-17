package solution

import "testing"

func Test_stairs_one(t *testing.T) {
	runCase(t, func() interface{} { return ClimbStairs(1) }, 1)
}

func Test_stairs_two(t *testing.T) {
	runCase(t, func() interface{} { return ClimbStairs(2) }, 2)
}

func Test_stairs_five(t *testing.T) {
	runCase(t, func() interface{} { return ClimbStairs(5) }, 8)
}

func Test_coins_basic(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{1,2,5}, 11) }, 3)
}

func Test_coins_impossible(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{2}, 3) }, -1)
}

func Test_coins_zero_amount(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{1}, 0) }, 0)
}

func Test_coins_greedy_fails(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{1,3,4}, 6) }, 2)
}


package solution

import "testing"

func Test_hidden_stairs_zero(t *testing.T) {
	runCase(t, func() interface{} { return ClimbStairs(0) }, 1)
}

func Test_hidden_stairs_forty_five(t *testing.T) {
	runCase(t, func() interface{} { return ClimbStairs(45) }, 1836311903)
}

func Test_hidden_coins_empty_set(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{}, 5) }, -1)
}

func Test_hidden_coins_unreachable(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{5,10}, 7) }, -1)
}

func Test_hidden_coins_larger(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{186,419,83,408}, 6249) }, 20)
}

func Test_hidden_coins_many(t *testing.T) {
	runCase(t, func() interface{} { return MinCoins([]int{1,5,10,25}, 10000) }, 400)
}


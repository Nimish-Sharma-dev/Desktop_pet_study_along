package solution

import "testing"

func Test_path_chain(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(5, [][]int{{0,1},{1,2},{2,3},{3,4}}, 0, 4) }, 4)
}

func Test_path_uses_shortcut(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(5, [][]int{{0,1},{1,2},{2,3},{3,4},{0,4}}, 0, 3) }, 2)
}

func Test_path_unreachable(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(4, [][]int{{0,1},{2,3}}, 0, 3) }, -1)
}

func Test_path_same_node(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(3, [][]int{{0,1}}, 2, 2) }, 0)
}

func Test_components_two_pairs(t *testing.T) {
	runCase(t, func() interface{} { return CountComponents(5, [][]int{{0,1},{2,3}}) }, 3)
}

func Test_components_connected(t *testing.T) {
	runCase(t, func() interface{} { return CountComponents(3, [][]int{{0,1},{1,2}}) }, 1)
}


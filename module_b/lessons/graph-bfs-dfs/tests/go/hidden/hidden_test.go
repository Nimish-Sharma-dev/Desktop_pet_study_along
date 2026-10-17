package solution

import "testing"

func Test_hidden_path_cycle_terminates(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(4, [][]int{{0,1},{1,2},{2,3},{3,0}}, 0, 2) }, 2)
}

func Test_hidden_path_single_node(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(1, [][]int{}, 0, 0) }, 0)
}

func Test_hidden_path_long_chain(t *testing.T) {
	runCase(t, func() interface{} { return ShortestPath(3000, lessonChainEdges(3000), 0, 2999) }, 2999)
}

func Test_hidden_components_no_nodes(t *testing.T) {
	runCase(t, func() interface{} { return CountComponents(0, [][]int{}) }, 0)
}

func Test_hidden_components_cycle(t *testing.T) {
	runCase(t, func() interface{} { return CountComponents(4, [][]int{{0,1},{1,2},{2,3},{3,0}}) }, 1)
}

func Test_hidden_components_isolated(t *testing.T) {
	runCase(t, func() interface{} { return CountComponents(4, [][]int{}) }, 4)
}

func Test_hidden_components_deep_chain(t *testing.T) {
	runCase(t, func() interface{} { return CountComponents(3000, lessonChainEdges(3000)) }, 1)
}


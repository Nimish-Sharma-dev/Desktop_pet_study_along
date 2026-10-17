const { check } = require('./lessonkit');

test("hidden_path_cycle_terminates", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [4, [[0, 1], [1, 2], [2, 3], [3, 0]], 0, 2], 2);
});

test("hidden_path_single_node", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [1, [], 0, 0], 0);
});

test("hidden_path_long_chain", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [3000, {"gen": "chain_edges", "args": [3000]}, 0, 2999], 2999);
});

test("hidden_components_no_nodes", () => {
  check("countComponents", ["int", "int_list_list"], "int", [0, []], 0);
});

test("hidden_components_cycle", () => {
  check("countComponents", ["int", "int_list_list"], "int", [4, [[0, 1], [1, 2], [2, 3], [3, 0]]], 1);
});

test("hidden_components_isolated", () => {
  check("countComponents", ["int", "int_list_list"], "int", [4, []], 4);
});

test("hidden_components_deep_chain", () => {
  check("countComponents", ["int", "int_list_list"], "int", [3000, {"gen": "chain_edges", "args": [3000]}], 1);
});


const { check } = require('./lessonkit');

test("path_chain", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [5, [[0, 1], [1, 2], [2, 3], [3, 4]], 0, 4], 4);
});

test("path_uses_shortcut", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [5, [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]], 0, 3], 2);
});

test("path_unreachable", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [4, [[0, 1], [2, 3]], 0, 3], -1);
});

test("path_same_node", () => {
  check("shortestPath", ["int", "int_list_list", "int", "int"], "int", [3, [[0, 1]], 2, 2], 0);
});

test("components_two_pairs", () => {
  check("countComponents", ["int", "int_list_list"], "int", [5, [[0, 1], [2, 3]]], 3);
});

test("components_connected", () => {
  check("countComponents", ["int", "int_list_list"], "int", [3, [[0, 1], [1, 2]]], 1);
});


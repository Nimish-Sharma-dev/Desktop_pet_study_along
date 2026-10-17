const { check } = require('./lessonkit');

test("hidden_empty", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[], 5], []);
});

test("hidden_single_cannot_pair_with_itself", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[5], 10], []);
});

test("hidden_duplicates", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[1, 1, 3, 5], 2], [0, 1]);
});

test("hidden_negatives", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[-4, -1, 0, 3, 10], -5], [0, 1]);
});

test("hidden_large", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [{"gen": "range", "args": [0, 300000, 2]}, 1199994], [299998, 299999]);
});


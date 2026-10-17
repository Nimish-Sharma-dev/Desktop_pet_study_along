const { check } = require('./lessonkit');

test("hidden_empty", () => {
  check("binarySearch", ["int_list", "int"], "int", [[], 3], -1);
});

test("hidden_single_found", () => {
  check("binarySearch", ["int_list", "int"], "int", [[4], 4], 0);
});

test("hidden_single_missing", () => {
  check("binarySearch", ["int_list", "int"], "int", [[4], 7], -1);
});

test("hidden_two_elements", () => {
  check("binarySearch", ["int_list", "int"], "int", [[1, 3], 3], 1);
});

test("hidden_below_min", () => {
  check("binarySearch", ["int_list", "int"], "int", [[5, 6, 7], 1], -1);
});

test("hidden_large", () => {
  check("binarySearch", ["int_list", "int"], "int", [{"gen": "range", "args": [0, 1000000, 1]}, 999999], 999999);
});


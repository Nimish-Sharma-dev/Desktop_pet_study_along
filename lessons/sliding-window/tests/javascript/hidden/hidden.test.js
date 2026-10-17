const { check } = require('./lessonkit');

test("hidden_window_is_whole_list", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[1, 2, 3], 3], 6);
});

test("hidden_window_too_big", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[1, 2], 5], 0);
});

test("hidden_empty", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[], 3], 0);
});

test("hidden_zero_window", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[1, 2, 3], 0], 0);
});

test("hidden_large", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [{"gen": "range", "args": [0, 1500000, 1]}, 5000], 7487497500);
});


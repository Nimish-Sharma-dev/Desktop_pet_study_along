const { check } = require('./lessonkit');

test("basic", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[1, 4, 2, 10, 2, 3, 1, 0, 20], 4], 24);
});

test("small_window", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[2, 1, 5, 1, 3, 2], 3], 9);
});

test("one_element", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[5], 1], 5);
});

test("all_negative", () => {
  check("maxWindowSum", ["int_list", "int"], "long", [[-3, -1, -2], 2], -3);
});


const { check } = require('./lessonkit');

test("found_middle", () => {
  check("binarySearch", ["int_list", "int"], "int", [[1, 3, 5, 7, 9], 5], 2);
});

test("found_first", () => {
  check("binarySearch", ["int_list", "int"], "int", [[1, 3, 5, 7, 9], 1], 0);
});

test("found_last", () => {
  check("binarySearch", ["int_list", "int"], "int", [[1, 3, 5, 7, 9], 9], 4);
});

test("not_found_inside", () => {
  check("binarySearch", ["int_list", "int"], "int", [[1, 3, 5, 7, 9], 4], -1);
});

test("not_found_above", () => {
  check("binarySearch", ["int_list", "int"], "int", [[1, 3, 5, 7, 9], 10], -1);
});


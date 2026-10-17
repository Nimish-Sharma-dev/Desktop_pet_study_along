const { check } = require('./lessonkit');

test("basic", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[2, 7, 11, 15], 9], [0, 1]);
});

test("middle_pair", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[1, 2, 4, 6, 10], 8], [1, 3]);
});

test("outer_pair", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[1, 3, 4, 8], 9], [0, 3]);
});

test("no_pair", () => {
  check("twoSumSorted", ["int_list", "int"], "int_list", [[1, 2, 3], 10], []);
});


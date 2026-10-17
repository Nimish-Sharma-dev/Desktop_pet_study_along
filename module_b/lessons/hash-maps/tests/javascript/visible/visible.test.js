const { check } = require('./lessonkit');

test("sum_basic", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[2, 7, 11, 15], 9], [0, 1]);
});

test("sum_not_first", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[3, 2, 4], 6], [1, 2]);
});

test("sum_duplicates", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[3, 3], 6], [0, 1]);
});

test("sum_none", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[1, 2, 3], 7], []);
});

test("anagram_yes", () => {
  check("isAnagram", ["string", "string"], "bool", ["listen", "silent"], true);
});

test("anagram_no", () => {
  check("isAnagram", ["string", "string"], "bool", ["rat", "car"], false);
});


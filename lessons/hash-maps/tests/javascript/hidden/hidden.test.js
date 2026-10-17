const { check } = require('./lessonkit');

test("hidden_sum_empty", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[], 4], []);
});

test("hidden_sum_no_self_reuse", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[5], 10], []);
});

test("hidden_sum_negatives", () => {
  check("twoSum", ["int_list", "int"], "int_list", [[-3, 4, 3, 90], 0], [0, 2]);
});

test("hidden_sum_large", () => {
  check("twoSum", ["int_list", "int"], "int_list", [{"gen": "range", "args": [0, 300000, 1]}, 599997], [299998, 299999]);
});

test("hidden_anagram_empty", () => {
  check("isAnagram", ["string", "string"], "bool", ["", ""], true);
});

test("hidden_anagram_length_differs", () => {
  check("isAnagram", ["string", "string"], "bool", ["a", "ab"], false);
});

test("hidden_anagram_same_letters_different_counts", () => {
  check("isAnagram", ["string", "string"], "bool", ["aacc", "ccac"], false);
});


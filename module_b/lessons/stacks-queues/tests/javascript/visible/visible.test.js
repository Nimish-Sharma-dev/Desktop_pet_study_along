const { check } = require('./lessonkit');

test("valid_simple", () => {
  check("isValidParentheses", ["string"], "bool", ["()"], true);
});

test("valid_mixed", () => {
  check("isValidParentheses", ["string"], "bool", ["()[]{}"], true);
});

test("valid_nested", () => {
  check("isValidParentheses", ["string"], "bool", ["{[]}"], true);
});

test("invalid_wrong_type", () => {
  check("isValidParentheses", ["string"], "bool", ["(]"], false);
});

test("invalid_interleaved", () => {
  check("isValidParentheses", ["string"], "bool", ["([)]"], false);
});

test("temps_example", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[73, 74, 75, 71, 69, 72, 76, 73]], [1, 1, 4, 2, 1, 1, 0, 0]);
});

test("temps_rising", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[30, 40, 50, 60]], [1, 1, 1, 0]);
});

test("temps_short", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[30, 60, 90]], [1, 1, 0]);
});


const { check } = require('./lessonkit');

test("hidden_empty_string", () => {
  check("isValidParentheses", ["string"], "bool", [""], true);
});

test("hidden_only_open", () => {
  check("isValidParentheses", ["string"], "bool", ["(("], false);
});

test("hidden_close_first", () => {
  check("isValidParentheses", ["string"], "bool", [")("], false);
});

test("hidden_only_close", () => {
  check("isValidParentheses", ["string"], "bool", ["]"], false);
});

test("hidden_unclosed_after_valid", () => {
  check("isValidParentheses", ["string"], "bool", ["()["], false);
});

test("hidden_temps_empty", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[]], []);
});

test("hidden_temps_single", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[5]], [0]);
});

test("hidden_temps_falling", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[5, 4, 3]], [0, 0, 0]);
});

test("hidden_temps_equal", () => {
  check("dailyTemperatures", ["int_list"], "int_list", [[5, 5, 5]], [0, 0, 0]);
});


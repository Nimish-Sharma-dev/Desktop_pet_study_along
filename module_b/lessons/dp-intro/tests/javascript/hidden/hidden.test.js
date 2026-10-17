const { check } = require('./lessonkit');

test("hidden_stairs_zero", () => {
  check("climbStairs", ["int"], "int", [0], 1);
});

test("hidden_stairs_forty_five", () => {
  check("climbStairs", ["int"], "int", [45], 1836311903);
});

test("hidden_coins_empty_set", () => {
  check("minCoins", ["int_list", "int"], "int", [[], 5], -1);
});

test("hidden_coins_unreachable", () => {
  check("minCoins", ["int_list", "int"], "int", [[5, 10], 7], -1);
});

test("hidden_coins_larger", () => {
  check("minCoins", ["int_list", "int"], "int", [[186, 419, 83, 408], 6249], 20);
});

test("hidden_coins_many", () => {
  check("minCoins", ["int_list", "int"], "int", [[1, 5, 10, 25], 10000], 400);
});


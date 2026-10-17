const { check } = require('./lessonkit');

test("stairs_one", () => {
  check("climbStairs", ["int"], "int", [1], 1);
});

test("stairs_two", () => {
  check("climbStairs", ["int"], "int", [2], 2);
});

test("stairs_five", () => {
  check("climbStairs", ["int"], "int", [5], 8);
});

test("coins_basic", () => {
  check("minCoins", ["int_list", "int"], "int", [[1, 2, 5], 11], 3);
});

test("coins_impossible", () => {
  check("minCoins", ["int_list", "int"], "int", [[2], 3], -1);
});

test("coins_zero_amount", () => {
  check("minCoins", ["int_list", "int"], "int", [[1], 0], 0);
});

test("coins_greedy_fails", () => {
  check("minCoins", ["int_list", "int"], "int", [[1, 3, 4], 6], 2);
});


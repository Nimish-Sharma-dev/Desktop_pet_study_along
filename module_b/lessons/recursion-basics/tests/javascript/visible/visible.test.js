const { check } = require('./lessonkit');

test("fib_zero", () => {
  check("fib", ["int"], "int", [0], 0);
});

test("fib_one", () => {
  check("fib", ["int"], "int", [1], 1);
});

test("fib_two", () => {
  check("fib", ["int"], "int", [2], 1);
});

test("fib_ten", () => {
  check("fib", ["int"], "int", [10], 55);
});

test("digits_zero", () => {
  check("sumDigits", ["int"], "int", [0], 0);
});

test("digits_single", () => {
  check("sumDigits", ["int"], "int", [7], 7);
});

test("digits_123", () => {
  check("sumDigits", ["int"], "int", [123], 6);
});

test("digits_9999", () => {
  check("sumDigits", ["int"], "int", [9999], 36);
});


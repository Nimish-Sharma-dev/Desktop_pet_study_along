const { check } = require('./lessonkit');

test("hidden_fib_twenty", () => {
  check("fib", ["int"], "int", [20], 6765);
});

test("hidden_fib_thirty", () => {
  check("fib", ["int"], "int", [30], 832040);
});

test("hidden_digits_power_of_ten", () => {
  check("sumDigits", ["int"], "int", [1000000], 1);
});

test("hidden_digits_ten", () => {
  check("sumDigits", ["int"], "int", [10], 1);
});


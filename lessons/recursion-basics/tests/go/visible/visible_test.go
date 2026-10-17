package solution

import "testing"

func Test_fib_zero(t *testing.T) {
	runCase(t, func() interface{} { return Fib(0) }, 0)
}

func Test_fib_one(t *testing.T) {
	runCase(t, func() interface{} { return Fib(1) }, 1)
}

func Test_fib_two(t *testing.T) {
	runCase(t, func() interface{} { return Fib(2) }, 1)
}

func Test_fib_ten(t *testing.T) {
	runCase(t, func() interface{} { return Fib(10) }, 55)
}

func Test_digits_zero(t *testing.T) {
	runCase(t, func() interface{} { return SumDigits(0) }, 0)
}

func Test_digits_single(t *testing.T) {
	runCase(t, func() interface{} { return SumDigits(7) }, 7)
}

func Test_digits_123(t *testing.T) {
	runCase(t, func() interface{} { return SumDigits(123) }, 6)
}

func Test_digits_9999(t *testing.T) {
	runCase(t, func() interface{} { return SumDigits(9999) }, 36)
}


package solution

import "testing"

func Test_hidden_fib_twenty(t *testing.T) {
	runCase(t, func() interface{} { return Fib(20) }, 6765)
}

func Test_hidden_fib_thirty(t *testing.T) {
	runCase(t, func() interface{} { return Fib(30) }, 832040)
}

func Test_hidden_digits_power_of_ten(t *testing.T) {
	runCase(t, func() interface{} { return SumDigits(1000000) }, 1)
}

func Test_hidden_digits_ten(t *testing.T) {
	runCase(t, func() interface{} { return SumDigits(10) }, 1)
}


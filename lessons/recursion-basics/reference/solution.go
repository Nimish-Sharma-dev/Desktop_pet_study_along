package solution

func Fib(n int) int {
	if n <= 1 {
		return n
	}
	return Fib(n-1) + Fib(n-2)
}

func SumDigits(n int) int {
	if n < 10 {
		return n
	}
	return n%10 + SumDigits(n/10)
}

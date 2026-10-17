def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


def sum_digits(n):
    if n < 10:
        return n
    return n % 10 + sum_digits(n // 10)

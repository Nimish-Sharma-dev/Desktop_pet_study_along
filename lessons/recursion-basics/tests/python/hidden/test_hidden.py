from lessonkit import check


def test_hidden_fib_twenty():
    check('fib', ['int'], 'int', [20], 6765)

def test_hidden_fib_thirty():
    check('fib', ['int'], 'int', [30], 832040)

def test_hidden_digits_power_of_ten():
    check('sum_digits', ['int'], 'int', [1000000], 1)

def test_hidden_digits_ten():
    check('sum_digits', ['int'], 'int', [10], 1)

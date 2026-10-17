from lessonkit import check


def test_fib_zero():
    check('fib', ['int'], 'int', [0], 0)

def test_fib_one():
    check('fib', ['int'], 'int', [1], 1)

def test_fib_two():
    check('fib', ['int'], 'int', [2], 1)

def test_fib_ten():
    check('fib', ['int'], 'int', [10], 55)

def test_digits_zero():
    check('sum_digits', ['int'], 'int', [0], 0)

def test_digits_single():
    check('sum_digits', ['int'], 'int', [7], 7)

def test_digits_123():
    check('sum_digits', ['int'], 'int', [123], 6)

def test_digits_9999():
    check('sum_digits', ['int'], 'int', [9999], 36)

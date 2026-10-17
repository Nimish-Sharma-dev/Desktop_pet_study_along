from lessonkit import check


def test_stairs_one():
    check('climb_stairs', ['int'], 'int', [1], 1)

def test_stairs_two():
    check('climb_stairs', ['int'], 'int', [2], 2)

def test_stairs_five():
    check('climb_stairs', ['int'], 'int', [5], 8)

def test_coins_basic():
    check('min_coins', ['int_list', 'int'], 'int', [[1, 2, 5], 11], 3)

def test_coins_impossible():
    check('min_coins', ['int_list', 'int'], 'int', [[2], 3], -1)

def test_coins_zero_amount():
    check('min_coins', ['int_list', 'int'], 'int', [[1], 0], 0)

def test_coins_greedy_fails():
    check('min_coins', ['int_list', 'int'], 'int', [[1, 3, 4], 6], 2)

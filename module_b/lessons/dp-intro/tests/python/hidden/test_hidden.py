from lessonkit import check


def test_hidden_stairs_zero():
    check('climb_stairs', ['int'], 'int', [0], 1)

def test_hidden_stairs_forty_five():
    check('climb_stairs', ['int'], 'int', [45], 1836311903)

def test_hidden_coins_empty_set():
    check('min_coins', ['int_list', 'int'], 'int', [[], 5], -1)

def test_hidden_coins_unreachable():
    check('min_coins', ['int_list', 'int'], 'int', [[5, 10], 7], -1)

def test_hidden_coins_larger():
    check('min_coins', ['int_list', 'int'], 'int', [[186, 419, 83, 408], 6249], 20)

def test_hidden_coins_many():
    check('min_coins', ['int_list', 'int'], 'int', [[1, 5, 10, 25], 10000], 400)

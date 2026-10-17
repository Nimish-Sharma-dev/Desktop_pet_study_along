from lessonkit import check


def test_valid_simple():
    check('is_valid_parentheses', ['string'], 'bool', ['()'], True)

def test_valid_mixed():
    check('is_valid_parentheses', ['string'], 'bool', ['()[]{}'], True)

def test_valid_nested():
    check('is_valid_parentheses', ['string'], 'bool', ['{[]}'], True)

def test_invalid_wrong_type():
    check('is_valid_parentheses', ['string'], 'bool', ['(]'], False)

def test_invalid_interleaved():
    check('is_valid_parentheses', ['string'], 'bool', ['([)]'], False)

def test_temps_example():
    check('daily_temperatures', ['int_list'], 'int_list', [[73, 74, 75, 71, 69, 72, 76, 73]], [1, 1, 4, 2, 1, 1, 0, 0])

def test_temps_rising():
    check('daily_temperatures', ['int_list'], 'int_list', [[30, 40, 50, 60]], [1, 1, 1, 0])

def test_temps_short():
    check('daily_temperatures', ['int_list'], 'int_list', [[30, 60, 90]], [1, 1, 0])

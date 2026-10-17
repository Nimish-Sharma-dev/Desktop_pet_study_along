from lessonkit import check


def test_hidden_empty_string():
    check('is_valid_parentheses', ['string'], 'bool', [''], True)

def test_hidden_only_open():
    check('is_valid_parentheses', ['string'], 'bool', ['(('], False)

def test_hidden_close_first():
    check('is_valid_parentheses', ['string'], 'bool', [')('], False)

def test_hidden_only_close():
    check('is_valid_parentheses', ['string'], 'bool', [']'], False)

def test_hidden_unclosed_after_valid():
    check('is_valid_parentheses', ['string'], 'bool', ['()['], False)

def test_hidden_temps_empty():
    check('daily_temperatures', ['int_list'], 'int_list', [[]], [])

def test_hidden_temps_single():
    check('daily_temperatures', ['int_list'], 'int_list', [[5]], [0])

def test_hidden_temps_falling():
    check('daily_temperatures', ['int_list'], 'int_list', [[5, 4, 3]], [0, 0, 0])

def test_hidden_temps_equal():
    check('daily_temperatures', ['int_list'], 'int_list', [[5, 5, 5]], [0, 0, 0])

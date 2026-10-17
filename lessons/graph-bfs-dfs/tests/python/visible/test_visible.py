from lessonkit import check


def test_path_chain():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [5, [[0, 1], [1, 2], [2, 3], [3, 4]], 0, 4], 4)

def test_path_uses_shortcut():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [5, [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]], 0, 3], 2)

def test_path_unreachable():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [4, [[0, 1], [2, 3]], 0, 3], -1)

def test_path_same_node():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [3, [[0, 1]], 2, 2], 0)

def test_components_two_pairs():
    check('count_components', ['int', 'int_list_list'], 'int', [5, [[0, 1], [2, 3]]], 3)

def test_components_connected():
    check('count_components', ['int', 'int_list_list'], 'int', [3, [[0, 1], [1, 2]]], 1)

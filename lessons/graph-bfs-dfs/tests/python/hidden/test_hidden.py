from lessonkit import check


def test_hidden_path_cycle_terminates():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [4, [[0, 1], [1, 2], [2, 3], [3, 0]], 0, 2], 2)

def test_hidden_path_single_node():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [1, [], 0, 0], 0)

def test_hidden_path_long_chain():
    check('shortest_path', ['int', 'int_list_list', 'int', 'int'], 'int', [3000, {'gen': 'chain_edges', 'args': [3000]}, 0, 2999], 2999)

def test_hidden_components_no_nodes():
    check('count_components', ['int', 'int_list_list'], 'int', [0, []], 0)

def test_hidden_components_cycle():
    check('count_components', ['int', 'int_list_list'], 'int', [4, [[0, 1], [1, 2], [2, 3], [3, 0]]], 1)

def test_hidden_components_isolated():
    check('count_components', ['int', 'int_list_list'], 'int', [4, []], 4)

def test_hidden_components_deep_chain():
    check('count_components', ['int', 'int_list_list'], 'int', [3000, {'gen': 'chain_edges', 'args': [3000]}], 1)

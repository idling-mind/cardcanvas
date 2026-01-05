
from cardcanvas.helpers import compare_dicts

def test_compare_dicts_equal():
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"a": 1, "b": {"c": 2}}
    assert compare_dicts(dict1, dict2)

def test_compare_dicts_not_equal_value():
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"a": 1, "b": {"c": 3}}
    assert not compare_dicts(dict1, dict2)

def test_compare_dicts_not_equal_keys():
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"a": 1, "d": 2}
    assert not compare_dicts(dict1, dict2)

def test_compare_dicts_nested_list():
    dict1 = {"a": [1, 2, {"x": 10}]}
    dict2 = {"a": [1, 2, {"x": 10}]}
    assert compare_dicts(dict1, dict2)

def test_compare_dicts_nested_list_diff():
    dict1 = {"a": [1, 2, {"x": 10}]}
    dict2 = {"a": [1, 2, {"x": 11}]}
    assert not compare_dicts(dict1, dict2)

def test_compare_dicts_different_types():
    dict1 = {"a": 1}
    dict2 = ["a", 1]
    assert not compare_dicts(dict1, dict2)

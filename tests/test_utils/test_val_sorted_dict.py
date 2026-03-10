from pulsarity.utils.collections import ValueSortedDict


def test_basic_features():
    """
    Test adding val
    """
    vals = (1, 2, 3)

    dict_ = ValueSortedDict()
    for val in vals:
        dict_[val] = val

    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)

    for val in vals:
        del dict_[val]

    assert len(dict_) == 0
    assert len(dict_.list) == 0


def test_from_tuple():
    """
    Test building dict from tuple
    """

    vals = (1, 2, 3)
    dict_ = ValueSortedDict((val, val) for val in vals)
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)


def test_from_mapping():
    """
    Test building dict from mapping
    """

    vals = (1, 2, 3)
    dict_ = ValueSortedDict({val: val for val in vals})
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)


def test_sort_by_value():
    """
    Test value is sorted when added
    """

    keys = range(100)
    values = reversed(keys)

    dict_ = ValueSortedDict()
    for key, val in zip(keys, values):
        dict_[key] = val

    assert dict_.keys()[:] != dict_.values()[:]
    assert dict_.values()[0] < dict_.values()[1]
    assert dict_.values()[-2] < dict_.values()[-1]


def test_sort_by_value_from_iterable():
    """
    Test values are sorted when instantiated
    """
    keys = range(100)
    values = reversed(keys)
    dict_ = ValueSortedDict((key, val) for key, val in zip(keys, values))
    assert dict_.keys()[:] != dict_.values()[:]
    assert dict_.values()[0] < dict_.values()[1]
    assert dict_.values()[-2] < dict_.values()[-1]


def test_sort_basic_sort():
    """
    Test keys and values are sorted
    """
    vals = (1, 3, 2)
    dict_ = ValueSortedDict()
    for val in vals:
        dict_[val] = val
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)

    assert dict_.keys()[:] == [1, 2, 3]
    assert dict_.values()[:] == [1, 2, 3]
    assert dict_.items()[:] == [(1, 1), (2, 2), (3, 3)]


def test_sort_basic_sort_from_tuple():
    """
    Test keys and values are sorted when created from tuple
    """
    vals = (1, 3, 2)
    dict_ = ValueSortedDict((val, val) for val in vals)
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)

    assert dict_.keys()[:] == [1, 2, 3]
    assert dict_.values()[:] == [1, 2, 3]
    assert dict_.items()[:] == [(1, 1), (2, 2), (3, 3)]


def test_sort_basic_sort_from_mapping():
    """
    Test keys and values are sorted when created from mapping
    """
    vals = (1, 3, 2)
    dict_ = ValueSortedDict((val, val) for val in vals)
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)

    assert dict_.keys()[:] == [1, 2, 3]
    assert dict_.values()[:] == [1, 2, 3]
    assert dict_.items()[:] == [(1, 1), (2, 2), (3, 3)]


def test_pop():
    """
    Test pop from key
    """
    vals = (1, 3, 2)
    dict_ = ValueSortedDict((val, val) for val in vals)
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)

    assert dict_.pop(1) == 1
    assert len(dict_) == len(vals) - 1
    assert len(dict_.list) == len(vals) - 1

    assert dict_.pop(3) == 3
    assert len(dict_) == len(vals) - 2
    assert len(dict_.list) == len(vals) - 2

    assert dict_.pop(2) == 2
    assert len(dict_) == len(vals) - 3
    assert len(dict_.list) == len(vals) - 3


def test_popitem():
    """
    Test popitem
    """
    vals = (1, 3, 2)
    dict_ = ValueSortedDict((val, val) for val in vals)
    assert len(dict_) == len(vals)
    assert len(dict_.list) == len(vals)

    assert dict_.popitem() == (3, 3)
    assert len(dict_) == len(vals) - 1
    assert len(dict_.list) == len(vals) - 1

    assert dict_.popitem() == (2, 2)
    assert len(dict_) == len(vals) - 2
    assert len(dict_.list) == len(vals) - 2

    assert dict_.popitem() == (1, 1)
    assert len(dict_) == len(vals) - 3
    assert len(dict_.list) == len(vals) - 3


def test_dict_operators():
    """
    Test updating and operators
    """
    vals1 = (1, 3, 5)
    dict1 = ValueSortedDict((val, val) for val in vals1)
    assert len(dict1) == 3
    assert len(dict1.list) == 3

    vals2 = (0, 2, 4)
    dict2 = ValueSortedDict((val, val) for val in vals2)
    assert len(dict2) == 3
    assert len(dict2.list) == 3

    dict3 = dict1 | dict2
    assert len(dict3) == 6
    assert len(dict3.list) == 6
    assert dict3.keys()[:] == [0, 1, 2, 3, 4, 5]

    assert len(dict1) == 3
    assert len(dict1.list) == 3
    dict1.update(dict2)
    assert len(dict1) == 6
    assert len(dict1.list) == 6
    assert dict1.keys()[:] == [0, 1, 2, 3, 4, 5]

    assert len(dict2) == 3
    assert len(dict2.list) == 3
    dict2 |= dict1
    assert len(dict2) == 6
    assert len(dict2.list) == 6
    assert dict2.keys()[:] == [0, 1, 2, 3, 4, 5]


def test_basic_copy():
    vals1 = (1, 3, 5)
    dict1 = ValueSortedDict((val, val) for val in vals1)
    assert len(dict1) == 3
    assert len(dict1.list) == 3

    dict2 = dict1.copy()
    assert dict1 == dict2
    assert dict1.list == dict2.list

    assert dict1 is not dict2
    assert dict1.list is not dict2.list


def test_clear():
    vals1 = (1, 3, 5)
    dict1 = ValueSortedDict((val, val) for val in vals1)
    assert len(dict1) == 3
    assert len(dict1.list) == 3

    dict1.clear()
    assert len(dict1) == 0
    assert len(dict1.list) == 0

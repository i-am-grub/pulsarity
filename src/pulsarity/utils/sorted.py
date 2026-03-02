"""
Custom sorted collections
"""

import bisect
from collections import UserDict
from collections.abc import ItemsView, KeysView, ValuesView
from typing import TypeVar

U = TypeVar("U")
V = TypeVar("V")


class SortedKeysView(KeysView[U]):
    """
    Sorted keys view of `ValueSortedDict`
    """

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    def __getitem__(self, index):
        return self._mapping.list[index]


class SortedValuesView(ValuesView[U]):
    """
    Sorted values view of `ValueSortedDict`
    """

    # pylint: disable=R0903

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    def __getitem__(self, index):
        if isinstance(index, slice):
            keys = self._mapping.list[index]
            return [self._mapping[key] for key in keys]

        key = self._mapping.list[index]
        return self._mapping[key]


class SortedItemsView(ItemsView[U, V]):
    """
    Sorted values view of `ValueSortedDict`
    """

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    def __getitem__(self, index):
        if isinstance(index, slice):
            keys = self._mapping.list[index]
            return [(key, self._mapping[key]) for key in keys]

        key = self._mapping.list[index]
        return key, self._mapping[key]


class ValueSortedDict(UserDict[U, V]):
    """
    Dictionary with sorted values
    """

    def __init__(self):
        super().__init__()
        self.list = []

    def __setitem__(self, key, item):
        if key in self:
            self.list.remove(key)
        super().__setitem__(key, item)
        bisect.insort_right(self.list, key, key=lambda x: self[x])

    def __delitem__(self, key):
        super().__delitem__(key)
        self.list.remove(key)

    def clear(self):
        super().clear()
        self.list.clear()

    def keys(self) -> SortedKeysView[U]:
        return SortedKeysView(self)

    def values(self) -> SortedValuesView[V]:
        return SortedValuesView(self)

    def items(self) -> SortedItemsView[U, V]:
        return SortedItemsView(self)

    def first_value(self) -> V:
        """
        Gets the first value in the sorted mapping
        """
        return self[self.list[0]]

    def last_value(self) -> V:
        """
        Gets the last value in the sorted mapping
        """
        return self[self.list[-1]]

    def update(self, **kwargs):
        raise NotImplementedError()

    def copy(self):
        raise NotImplementedError()

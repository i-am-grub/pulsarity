"""
Custom collections
"""

import bisect
from collections import UserDict
from collections.abc import ItemsView, Iterable, KeysView, ValuesView
from typing import TypeVar

U = TypeVar("U")
V = TypeVar("V")


class SortedKeysView(KeysView[U]):
    """
    Sorted keys view of `ValueSortedDict`
    """

    __slots__ = ("_mapping",)

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    def __getitem__(self, index):
        return self._mapping.list[index]


class SortedValuesView(ValuesView[U]):
    """
    Sorted values view of `ValueSortedDict`
    """

    __slots__ = ("_mapping",)

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    def __getitem__(self, index):
        if isinstance(index, slice):
            keys = self._mapping.list[index]
            return [self._mapping.data[key] for key in keys]

        key = self._mapping.list[index]
        return self._mapping.data[key]


class SortedItemsView(ItemsView[U, V]):
    """
    Sorted values view of `ValueSortedDict`
    """

    __slots__ = ("_mapping",)

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    def __getitem__(self, index):
        if isinstance(index, slice):
            keys = self._mapping.list[index]
            return [(key, self._mapping.data[key]) for key in keys]

        key = self._mapping.list[index]
        return key, self._mapping.data[key]


class ValueSortedDict(UserDict[U, V]):
    """
    Dictionary with sorted values
    """

    __slots__ = ("data", "list")

    def __init__(self, iterable: Iterable[tuple[U, V]] | None = None):
        self.list = []
        if iterable is None:
            super().__init__()
        elif isinstance(iterable, Iterable):
            super().__init__(iterable)
            self.list = sorted(self.data.keys(), key=self._by_value_key)  # type: ignore
        else:
            raise ValueError("Unsupported input value")

    def _by_value_key(self, key: U) -> V:
        return self.data[key]

    def __setitem__(self, key, item):
        if key in self.data:
            self.list.remove(key)

        self.data[key] = item

        if not self.list or self.data[key] >= self.data[self.list[-1]]:
            self.list.append(key)
        else:
            bisect.insort_right(self.list, key, key=self._by_value_key)

    def __delitem__(self, key):
        del self.data[key]
        self.list.remove(key)

    def clear(self):
        self.data.clear()
        self.list.clear()

    def keys(self) -> SortedKeysView[U]:
        return SortedKeysView(self)

    def values(self) -> SortedValuesView[V]:
        return SortedValuesView(self)

    def items(self) -> SortedItemsView[U, V]:
        return SortedItemsView(self)

    def peek_value(self, index: int = -1) -> V:
        """
        Peeks the value at an index in the sorted mapping

        :param index: Index to peek the value at, defaults to -1
        :return: The value
        """
        return self.data[self.list[index]]

    def popitem(self):
        key = self.list.pop()
        return key, self.data.pop(key)

    def update(self, mapping):
        # pylint: disable=W0221
        self.data.update(mapping)
        self.list = sorted(self.data.keys(), key=self._by_value_key)

    def copy(self):
        copy_ = self.__class__()
        copy_.data = self.data.copy()
        copy_.list = self.list.copy()
        return copy_

    def __iter__(self):
        return self.list.__iter__()

    def __reversed__(self):
        return self.list.__reversed__()

    def __repr__(self):
        vals = [f"{key}: {self.data[key]}" for key in self.list]
        return f"{{{', '.join(vals)}}}"

    def __ior__(self, other):  # type: ignore
        super().__ior__(other)
        self.list = sorted(self.data.keys(), key=self._by_value_key)
        return self

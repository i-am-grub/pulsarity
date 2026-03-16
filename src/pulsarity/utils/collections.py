"""Custom collections"""

import bisect
from collections.abc import ItemsView, Iterable, KeysView, ValuesView
from typing import TypeVar, overload, override

U = TypeVar("U")
V = TypeVar("V")


class SortedKeysView(KeysView[U]):
    """Sorted keys view of `ValueSortedDict`"""

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    @overload
    def __getitem__(self, i: int) -> U: ...
    @overload
    def __getitem__(self, s: slice) -> list[U]: ...
    def __getitem__(self, index):
        return self._mapping.list[index]


class SortedValuesView(ValuesView[U]):
    """Sorted values view of `ValueSortedDict`"""

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    @overload
    def __getitem__(self, i: int) -> U: ...
    @overload
    def __getitem__(self, s: slice) -> list[U]: ...
    def __getitem__(self, index):
        if isinstance(index, slice):
            keys = self._mapping.list[index]
            return [self._mapping[key] for key in keys]

        key = self._mapping.list[index]
        return self._mapping[key]


class SortedItemsView(ItemsView[U, V]):
    """Sorted values view of `ValueSortedDict`"""

    def __init__(self, mapping: ValueSortedDict):
        super().__init__(mapping)
        self._mapping = mapping

    @overload
    def __getitem__(self, i: int) -> tuple[U, V]: ...
    @overload
    def __getitem__(self, s: slice) -> list[tuple[U, V]]: ...
    def __getitem__(self, index):
        if isinstance(index, slice):
            keys = self._mapping.list[index]
            return [(key, self._mapping[key]) for key in keys]

        key = self._mapping.list[index]
        return key, self._mapping[key]


class ValueSortedDict(dict[U, V]):
    """Dictionary with sorted values"""

    __slots__ = ("list",)
    __marker = object()

    def __init__(self, iterable: Iterable[tuple[U, V]] | None = None):
        self.list: list[U] = []
        if iterable is None:
            super().__init__()
        elif isinstance(iterable, Iterable):
            super().__init__(iterable)
            self.list = sorted(super().keys(), key=self._by_value_key)  # type: ignore
        else:
            msg = f"{type(iterable)} object is not iterable"
            raise TypeError(msg)

    def _by_value_key(self, key: U) -> V:
        return self[key]

    @override
    def __setitem__(self, key, item):
        if key in self:
            self.list.remove(key)

        super().__setitem__(key, item)

        if not self.list or self[key] >= self[self.list[-1]]:
            self.list.append(key)
        else:
            bisect.insort_right(self.list, key, key=self._by_value_key)

    @override
    def __delitem__(self, key):
        super().__delitem__(key)
        self.list.remove(key)

    @override
    def clear(self):
        super().clear()
        self.list.clear()

    @override
    def keys(self) -> SortedKeysView[U]:  # type: ignore
        return SortedKeysView(self)

    @override
    def values(self) -> SortedValuesView[V]:  # type: ignore
        return SortedValuesView(self)

    @override
    def items(self) -> SortedItemsView[U, V]:  # type: ignore
        return SortedItemsView(self)

    @override
    def pop(self, key, default=__marker):
        marker = self.__marker
        result = super().pop(key, marker)
        if result is not marker:
            self.list.remove(key)
            return result
        if default is marker:
            raise KeyError(key)
        return default

    @override
    def popitem(self):
        key = self.list.pop()
        return key, super().pop(key)

    @override
    def update(self, mapping):
        super_ = super()
        super_.update(mapping)
        self.list = sorted(super_.keys(), key=self._by_value_key)

    @override
    def copy(self):
        copy_ = self.__class__()
        copy_.update(self)
        return copy_

    @override
    def __iter__(self):
        return self.list.__iter__()

    @override
    def __reversed__(self):
        return self.list.__reversed__()

    @override
    def __repr__(self):
        vals = [f"{key}: {self[key]}" for key in self.list]
        return f"{{{', '.join(vals)}}}"

    @override
    def __or__(self, other):
        new = super().__or__(other)
        return self.__class__(new)

    @override
    def __ror__(self, other):
        new = super().__ror__(other)
        return self.__class__(new)

    @override
    def __ior__(self, other):
        super_ = super()
        super_.__ior__(other)
        self.list = sorted(super_.keys(), key=self._by_value_key)
        return self

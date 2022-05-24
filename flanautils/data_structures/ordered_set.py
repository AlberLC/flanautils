from __future__ import annotations  # todo0 remove in 3.11

import itertools
import json
import math
import pickle
from typing import AbstractSet, Any, Generic, Iterable, Iterator, MutableSet, Type, TypeVar

from flanautils import iterables
from flanautils.models.bases import FlanaBase, JSONBASE

E = TypeVar('E')


class OrderedSet(FlanaBase, MutableSet, Generic[E]):
    """
    Set that maintains the insertion order.

    Reimplements all set and list methods.

    Note that being built on hashes, the list methods are not efficient since the sets are not designed to access a
    specific element of the structure.
    """

    FLATTEN_DEPTH = 1

    T = TypeVar('T', bound='OrdereSet')

    def __init__(self, *args: Any):
        self._elements_dict = {element: None for element in iterables.flatten_iterator(*args, depth=self.FLATTEN_DEPTH)}

    def __add__(self, other) -> OrderedSet[E]:
        return self | other

    def __iadd__(self, other):
        return self.__ior__(other)

    def __radd__(self, other) -> OrderedSet[E]:
        return other | self

    def __and__(self, other) -> OrderedSet[E]:
        return OrderedSet(value for value in self if value in self.ordered_set_if_not_set(other))

    def __iand__(self, other):
        for value in (self - self.ordered_set_if_not_set(other)):
            self.discard(value)
        return self

    def __rand__(self, other) -> OrderedSet[E]:
        return self.ordered_set_if_not_set(other) & self

    def __contains__(self, element: Any) -> bool:
        return element in self._elements_dict

    def __delitem__(self, item):
        if isinstance(item, slice):
            self.discard_many(self[item])
        else:
            self.discard(self[item])

    def __eq__(self, other) -> bool:
        if not isinstance(other, OrderedSet):
            return False

        for self_element, other_element in itertools.zip_longest(self, other):
            if self_element != other_element:
                return False
        return True

    def __getitem__(self, item) -> E | OrderedSet[E]:
        ordered_set = OrderedSet()
        len_self = len(self)

        if isinstance(item, slice):
            step = 1 if item.step is None else item.step
            if step > 0:
                if item.start is None:
                    start = 0
                else:
                    start = self.positive_index(item.start)
                    if start >= len_self:
                        return ordered_set
                    start = max(0, start)

                if item.stop is None:
                    stop = len_self
                else:
                    stop = self.positive_index(item.stop)
                    if stop <= 0:
                        return ordered_set
                    stop = min(stop, len_self)

                iterator = iter(self)

            elif step < 0:
                if item.start is None:
                    start = 0
                else:
                    start = self.positive_index(item.start)
                    if start < 0:
                        return ordered_set
                    start = len_self - 1 - min(start, len_self - 1)

                if item.stop is None:
                    stop = len_self
                else:
                    stop = self.positive_index(item.stop)
                    if stop >= len_self - 1:
                        return ordered_set
                    stop = len_self - 1 - max(-1, stop)

                step *= -1

                iterator = reversed(self)

            else:
                raise ValueError('slice step cannot be zero')

            iterables.iterate_n(iterator, start)
            for _ in range(math.ceil((stop - start) / step)):
                try:
                    ordered_set.add(next(iterator))
                    iterables.iterate_n(iterator, step - 1)
                except StopIteration:
                    break

            return ordered_set

        elif isinstance(item, int):
            item = self.positive_index(item)
            if not 0 <= item < len_self:
                raise IndexError('index out of range')

            if item <= len_self / 2:
                iterator = iter(self)
                index = item
            else:
                iterator = reversed(self)
                index = len_self - item - 1

            return iterables.iterate_n(iterator, index + 1)

        else:
            raise TypeError('indices must be integers or slices')

    def __iter__(self) -> Iterator[E]:
        return iter(self._elements_dict)

    def __len__(self) -> int:
        return len(self._elements_dict)

    def __or__(self, other) -> OrderedSet[E]:
        return OrderedSet(super().__or__(self.ordered_set_if_not_set(other)))

    def __ior__(self, other):
        for value in self.ordered_set_if_not_set(other):
            self.add(value)
        return self

    def __ror__(self, other) -> OrderedSet[E]:
        return self.ordered_set_if_not_set(other) | self

    def __repr__(self) -> str:
        return str(self)

    def __reversed__(self) -> Iterator[E]:
        return reversed(self._elements_dict)

    def __str__(self) -> str:
        return f"#{{{', '.join(repr(element) for element in self)}}}"

    def __sub__(self, other) -> OrderedSet[E]:
        return OrderedSet(super().__sub__(self.ordered_set_if_not_set(other)))

    def __isub__(self, other):
        if other is self:
            self.clear()
        else:
            for value in self.ordered_set_if_not_set(other):
                self.discard(value)
        return self

    def __rsub__(self, other) -> OrderedSet[E]:
        return self.ordered_set_if_not_set(other) - self

    def _json_repr(self) -> Any:
        return [json.loads(element.to_json()) if isinstance(element, JSONBASE) else pickle.dumps(element) for element in self]

    def positive_index(self, index_: int) -> int:
        if index_ < 0:
            index_ += len(self)
        return index_

    @classmethod
    def ordered_set_if_not_set(cls: Type[T], arg: Any) -> AbstractSet | T:
        return arg if isinstance(arg, AbstractSet) else cls(iterables.flatten_iterator(arg))

    def add(self, element: Any):
        self._elements_dict[element] = None

    def add_many(self, elements: Iterable):
        for element in elements:
            self.add(element)

    def clear(self):
        try:
            while True:
                self.pop()
        except IndexError:
            pass

    def copy(self) -> OrderedSet[E]:
        return OrderedSet(self)

    def difference(self, *args: Iterable) -> OrderedSet[E]:
        new_ordered_set = OrderedSet(self)
        new_ordered_set.difference_update(*args)
        return new_ordered_set

    def difference_update(self, *args: Iterable):
        self.discard_many(iterables.flatten_iterator(*args, depth=self.FLATTEN_DEPTH))

    def discard(self, element: Any):
        try:
            self._elements_dict.pop(element, None)
        except TypeError:
            pass

    def discard_many(self, elements: Iterable):
        for element in elements:
            self.discard(element)

    def index(self, element, start=None, stop=None, raise_exception=False) -> int:
        if start is not None or stop is not None:
            ordered_set = self[start:stop]
        else:
            ordered_set = self

        if start is None:
            start = 0
        else:
            start = max(0, start)

        for i, element_ in enumerate(ordered_set):
            if element == element_:
                return start + i

        if raise_exception:
            raise ValueError(f'{element} is not in the OrderedSet')

    def insert(self, i, element):
        if element in self:
            return

        i = self.positive_index(i)

        deleted_elements = []
        for i_, element_ in enumerate(list(self)):
            if i <= i_:
                self.discard(element_)
                deleted_elements.append(element_)

        self.add(element)
        self.add_many(deleted_elements)

    def intersection(self, *args: Iterable) -> OrderedSet[E]:
        new_ordered_set = OrderedSet(self)
        new_ordered_set.intersection_update(*args)
        return new_ordered_set

    def intersection_update(self, *args: Iterable):
        elements_to_delete = []
        for element in self:
            for arg in args:
                if element not in iterables.flatten_iterator(arg, depth=self.FLATTEN_DEPTH):
                    elements_to_delete.append(element)
                    break

        self.discard_many(elements_to_delete)

    def is_disjoint(self, other) -> bool:
        return not (self & other)

    def is_subset(self, other) -> bool:
        return self <= other

    def is_superset(self, other) -> bool:
        return self >= other

    def pop(self, index=-1) -> E:
        element = self[index]
        self.discard(element)
        return element

    def reverse(self):
        reversed_self = list(reversed(self))
        self.clear()
        self.add_many(reversed_self)

    def sort(self, key=None, reverse=False):
        sorted_values = sorted(self, key=key, reverse=reverse)
        self.clear()
        self.add_many(sorted_values)

    def symmetric_difference(self, *args: Iterable) -> OrderedSet[E]:
        new_ordered_set = OrderedSet(self)
        new_ordered_set.symmetric_difference_update(*args)
        return new_ordered_set

    def symmetric_difference_update(self, *args: Iterable):
        for arg in args:
            other_minus_self = self.ordered_set_if_not_set(arg) - self
            self.difference_update(arg)
            self.update(other_minus_self)

    def union(self, *args: Iterable) -> OrderedSet[E]:
        new_ordered_set = OrderedSet(self)
        new_ordered_set.update(*args)
        return new_ordered_set

    def update(self, *args: Iterable):
        self.add_many(iterables.flatten_iterator(*args, depth=self.FLATTEN_DEPTH))

    union_update = update

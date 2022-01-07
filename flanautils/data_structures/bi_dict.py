from __future__ import annotations  # todo0 remove in 3.11

from typing import Any, Iterable, Mapping


class BiDict(dict):
    """
    Dictionary that also stores an inverted dictionary to access efficiently through hashes in both directions
    (key -> value, value -> key).

    Reimplements all dictionary methods.
    """

    def __init__(self, dict_: dict = None):
        dict_ = {} if dict_ is None else dict_
        super().__init__(dict_)
        self.inverted = {v: k for k, v in dict_.items()}

    def __contains__(self, item):
        if exists := super().__contains__(item):
            return exists
        else:
            return item in self.inverted

    def __delitem__(self, item):
        value = self[item]
        try:
            super().__delitem__(item)
        except (KeyError, TypeError):
            del self.inverted[value]

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except (KeyError, TypeError):
            return self.inverted[item]

    def __or__(self, other):
        return BiDict(super().__or__(other))

    def __ror__(self, other):
        return BiDict(dict.__or__(other, self))

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{{{', '.join(f'{repr(k)}::{repr(v)}' for k, v in self.items())}}}"

    def clear(self):
        super().clear()
        self.inverted.clear()

    def copy(self) -> BiDict:
        return BiDict(self)

    @classmethod
    def fromkeys(cls, iterable: Iterable, value: Any = None) -> BiDict:
        return cls(dict.fromkeys(iterable, value))

    def get(self, key: Any, default: Any = None) -> Any:
        if (value := super().get(key, default)) == default:
            return self.inverted.get(key, default)
        else:
            return value

    def pop(self, key: Any) -> Any:
        try:
            return super().pop(key)
        except KeyError:
            return self.inverted.pop(key)

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key in self:
            return self[key]
        else:
            self[key] = default
            self.inverted[default] = key
            return default

    def union(self, mapping: Mapping | Iterable, **kwargs):
        new_bi_dict = BiDict(self)
        new_bi_dict.update(mapping, **kwargs)
        return new_bi_dict

    def update(self, mapping: Mapping | Iterable, **kwargs):
        if isinstance(mapping, Mapping):
            items = list(mapping.items())
        elif isinstance(mapping, Iterable):
            items = [(element[0], element[1]) for element in mapping]
        else:
            items = []
        items.extend(list(kwargs.items()))

        for k, v in items:
            self[k] = v
            self.inverted[v] = k

    union_update = update

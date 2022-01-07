from dataclasses import dataclass
from typing import Generic, TypeVar

from flanautils.models.bases import FlanaBase

T = TypeVar('T')


@dataclass(frozen=True)
class RatioMatch(FlanaBase, Generic[T]):
    """Dataclass to store the relationship between an element and a punctuation or ratio."""

    element: T
    ratio: float

    def __add__(self, other):
        other_value = other.ratio if isinstance(other, RatioMatch) else other
        return self.ratio + other_value

    def __radd__(self, other):
        return self + other

    def __eq__(self, other):
        if isinstance(other, RatioMatch):
            return (self.element, self.ratio) == (other.element, other.ratio)
        else:
            return self.element == other

    def __lt__(self, other):
        return (other.ratio, str(self.element)) < (self.ratio, str(other.element))

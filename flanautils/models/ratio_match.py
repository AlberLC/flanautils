from dataclasses import dataclass
from typing import Generic, TypeVar

from flanautils.models.bases import FlanaBase

T = TypeVar('T')


@dataclass(frozen=True)
class ScoreMatch(FlanaBase, Generic[T]):
    """Dataclass to store the relationship between an element and a score."""

    element: T
    score: float

    def __add__(self, other):
        other_value = other.score if isinstance(other, ScoreMatch) else other
        return self.score + other_value

    def __radd__(self, other):
        return self + other

    def __eq__(self, other):
        if isinstance(other, ScoreMatch):
            return (self.element, self.score) == (other.element, other.score)
        else:
            return self.element == other

    def __lt__(self, other):
        return (other.score, str(self.element)) < (self.score, str(other.element))

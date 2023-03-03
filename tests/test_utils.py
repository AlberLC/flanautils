import random
from typing import Iterable

from flanautils import strings


def random_elements(k=1) -> list:
    return [random.choice(
        (
            random.randint(-150, 150),
            random.uniform(-150, 150),
            strings.random_string(0, 5)
        )
    ) for _ in range(k)]


def random_collections(k=1) -> list:
    return [random.choice(
        (
            *random_elements(random.randint(0, 3)),
            (*random_elements(random.randint(0, 3)),),
            [*random_elements(random.randint(0, 3))],
            {*random_elements(random.randint(0, 3))}
        )
    ) for _ in range(k)]


def list_without_repetitions(*iterables: Iterable[Iterable]) -> list:
    result = []
    for iterable in iterables:
        for element in iterable:
            if element not in result:
                result.append(element)

    return result

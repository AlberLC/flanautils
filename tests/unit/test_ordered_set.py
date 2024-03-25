import itertools
import random
import unittest
from collections.abc import Callable
from typing import Iterable

import iterables
import strings
import test_utils
from data_structures.ordered_set import OrderedSet
from functions import repeat

REPEAT_TIMES = 500


class TestOrderedSet(unittest.TestCase):
    def _index_access_exceptions(self, ordered_set: OrderedSet, func: Callable):
        self.assertRaises(TypeError, func, strings.random_string(0, 5))
        self.assertRaises(TypeError, func, [random.randint(-50, 50) for _ in range(random.randint(-5, 5))])
        self.assertRaises(TypeError, func, tuple(random.randint(-50, 50) for _ in
                                                 range(random.randint(-5, 5))))
        self.assertRaises(TypeError, func, {random.randint(-50, 50) for _ in range(random.randint(-5, 5))})
        self.assertRaises(TypeError, func, {random.randint(-50, 50): random.randint(-50, 50) for _ in
                                            range(random.randint(-5, 5))})

        self.assertRaises(IndexError, func, random.randint(-len(ordered_set) - 50, -len(ordered_set) - 1))
        self.assertRaises(IndexError, func, random.randint(len(ordered_set), len(ordered_set) + 50))

    @staticmethod
    def _random_start_stop_step(flatten_elements: list):
        start = random.randint(-len(flatten_elements) - 50, len(flatten_elements) + 50) if random.random() <= 0.8 else None
        stop = random.randint(-len(flatten_elements) - 50, len(flatten_elements) + 50) if random.random() <= 0.8 else None
        while (
            step := random.randint(-len(flatten_elements) - 50, len(flatten_elements) + 50) if random.random() <= 0.8 else None
        ) == 0:
            pass

        return start, stop, step

    @staticmethod
    def _create_set_and_ordered_set():
        elements_s1 = test_utils.random_elements(random.randint(0, 5))
        flatten_elements_s1 = iterables.flatten(*elements_s1, lazy=True)
        return {*flatten_elements_s1}, OrderedSet(*elements_s1)

    def test_init(self):
        OrderedSet()
        OrderedSet(1)
        OrderedSet(1, 'asd')
        OrderedSet([2])
        OrderedSet(3, ['a'])
        OrderedSet(3, ['bb'], [5, ('asd',)])
        OrderedSet(3, [4], ('c', (6,)))

    def test_init_fail_list(self):
        self.assertRaises(TypeError, OrderedSet, 5, [6], [7, [8]])
        self.assertRaises(TypeError, OrderedSet, 5, [6], [(7,), [8]])

    def test_init_fail_set(self):
        self.assertRaises(TypeError, OrderedSet, [{5}])
        self.assertRaises(TypeError, OrderedSet, 5, ({6},))

    @repeat(REPEAT_TIMES)
    def test__add__and__iadd__and__radd__(self):
        elements_s1 = test_utils.random_collections(random.randint(0, 5))
        elements_s2 = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements_s1)
        s2 = OrderedSet(*elements_s2)

        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements_s1 + elements_s2, lazy=True))

        with self.subTest('__add__'):
            self.assertEqual(expected_elements, list(s1 + s2))
        with self.subTest('__iadd__'):
            s1 += s2
            self.assertEqual(expected_elements, list(s1))
        with self.subTest('__radd__'):
            self.assertEqual(expected_elements, list(elements_s1 + s2))

    @repeat(REPEAT_TIMES)
    def test__and__and__iand__and__rand__and_intersection_and_intersection_update(self):
        elements_s1 = test_utils.random_collections(random.randint(0, 5))
        elements_s2 = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements_s1)
        s2 = OrderedSet(*elements_s2)

        elements_s2_flatten = list(iterables.flatten(*elements_s2, lazy=True))
        expected_elements = []
        for element in iterables.flatten(*elements_s1, lazy=True):
            if element in elements_s2_flatten and element not in expected_elements:
                expected_elements.append(element)

        with self.subTest('__and__'):
            self.assertEqual(expected_elements, list(s1 & s2))
        with self.subTest('__iand__'):
            s1b = s1.copy()
            s1b &= s2
            self.assertEqual(expected_elements, list(s1b))
        with self.subTest('__rand__'):
            self.assertEqual(expected_elements, list(elements_s1 & s2))
        with self.subTest('intersection'):
            self.assertEqual(expected_elements, list(s1.intersection(s2)))
        with self.subTest('intersection_update'):
            s1.intersection_update(s2)
            self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test__contains__(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements)

        for element in iterables.flatten(elements, lazy=True):
            self.assertIn(element, s1)

    @repeat(REPEAT_TIMES)
    def test__del__(self):
        while not (elements := [element for element in test_utils.random_collections(random.randint(2, 15)) if element]):
            pass

        s1 = OrderedSet(*elements)
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        start, stop, step = self._random_start_stop_step(expected_elements)

        expected_elements_copy = expected_elements.copy()
        s1_copy = s1.copy()
        del expected_elements_copy[start:stop:step]
        del s1_copy[start:stop:step]
        self.assertEqual(expected_elements_copy, list(s1_copy))
        for i in range(-len(expected_elements), len(expected_elements)):
            with self.subTest(i=i):
                expected_elements_copy = expected_elements.copy()
                s1_copy = s1.copy()
                del expected_elements_copy[i]
                del s1_copy[i]
                self.assertEqual(expected_elements_copy, list(s1_copy))

        self._index_access_exceptions(s1, s1.__delitem__)

    @repeat(REPEAT_TIMES)
    def test__eq__(self):
        elements = test_utils.random_collections(random.randint(0, 10))

        self.assertEqual(OrderedSet(*elements), OrderedSet(*elements))

    @repeat(REPEAT_TIMES)
    def test__eq__fail(self):
        while True:
            elements = [element for element in test_utils.random_collections(random.randint(2, 15)) if element]
            if len(elements) < 2:
                continue

            flatten_elements = list(iterables.flatten(*elements, lazy=True))
            for i in range(len(flatten_elements) - 1):
                for j in range(i + 1, len(flatten_elements)):
                    if flatten_elements[i] == flatten_elements[j]:
                        break
                else:
                    continue
                break
            else:
                break

        while (shuffled_elements := random.sample(elements, k=len(elements))) == elements:
            pass

        self.assertNotEqual(OrderedSet(*elements), OrderedSet(*shuffled_elements))

    @repeat(REPEAT_TIMES)
    def test__getitem__(self):
        while not (
            elements := [element for element in test_utils.random_collections(random.randint(2, 15)) if element]
        ):
            pass

        s1 = OrderedSet(*elements)
        flatten_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        start, stop, step = self._random_start_stop_step(flatten_elements)

        self.assertEqual(flatten_elements[start:stop:step], list(s1[start:stop:step]))
        for i in range(-len(flatten_elements), len(flatten_elements)):
            with self.subTest(i=i):
                self.assertEqual(flatten_elements[i], s1[i])

        self._index_access_exceptions(s1, s1.__getitem__)

    @repeat(REPEAT_TIMES)
    def test__iter__(self):
        elements = test_utils.random_collections(random.randint(0, 15))
        s1 = OrderedSet(*elements)
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        self.assertIsInstance(s1, Iterable)
        self.assertEqual(expected_elements, list(s1))
        for expected_element, actual_element in itertools.zip_longest(expected_elements, s1):
            self.assertEqual(expected_element, actual_element)

    @repeat(REPEAT_TIMES)
    def test__len__(self):
        elements = test_utils.random_collections(random.randint(0, 15))

        self.assertEqual(len(list(test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True)))), len(OrderedSet(*elements)))

    @repeat(REPEAT_TIMES)
    def test__or__and__ior__and__ror__(self):
        elements_s1 = test_utils.random_collections(random.randint(0, 5))
        elements_s2 = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements_s1)
        s2 = OrderedSet(*elements_s2)

        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements_s1 + elements_s2, lazy=True))

        with self.subTest('__or__'):
            self.assertEqual(expected_elements, list(s1 | s2))
        with self.subTest('__ior__'):
            s1 |= s2
            self.assertEqual(expected_elements, list(s1))
        with self.subTest('__ror__'):
            self.assertEqual(expected_elements, list(elements_s1 | s2))

    def test__repr__(self):
        s1 = OrderedSet(*test_utils.random_collections(random.randint(0, 5)))

        self.assertEqual(str(s1), repr(s1))

    @repeat(REPEAT_TIMES)
    def test__reversed__(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        flatten_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))
        s1 = OrderedSet(*elements)

        self.assertEqual(list(reversed(flatten_elements)), list(reversed(s1)))

    def test__str__(self):
        self.assertEqual("#{1, 'a', ('bb', 25.4)}", str(OrderedSet(1, 'a', [('bb', 25.4)])))
        self.assertNotEqual("#{1, 'a', ('bb', 25.4)}", str(OrderedSet(1, 'a', [(25.4, 'bb')])))

    @repeat(REPEAT_TIMES)
    def test__sub__and__isub__and__rsub__and_difference_and_difference_update(self):
        elements_s1 = test_utils.random_collections(random.randint(0, 5))
        elements_s2 = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements_s1)
        s2 = OrderedSet(*elements_s2)

        flatten_elements_s2 = list(iterables.flatten(*elements_s2, lazy=True))

        expected_elements = test_utils.list_without_repetitions(
            element for element in iterables.flatten(*elements_s1, lazy=True) if element not in flatten_elements_s2
        )

        with self.subTest('__sub__'):
            self.assertEqual(expected_elements, list(s1 - s2))
        with self.subTest('__isub__'):
            s1b = s1.copy()
            s1b -= s2
            self.assertEqual(expected_elements, list(s1b))
        with self.subTest('__rsub__'):
            self.assertEqual(expected_elements, list(elements_s1 - s2))
        with self.subTest('difference'):
            self.assertEqual(expected_elements, list(s1.difference(s2)))
        with self.subTest('difference_update'):
            s1.difference_update(s2)
            self.assertEqual(expected_list, list(s1))
            self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test_ordered_set_if_not_set(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        flatten_elements = list(iterables.flatten(elements, lazy=True))

        result = OrderedSet.ensure_set({*flatten_elements})

        self.assertIsInstance(result, set)
        self.assertEqual({*flatten_elements}, result)
        result = OrderedSet.ensure_set(elements)
        self.assertIsInstance(result, OrderedSet)
        self.assertEqual(OrderedSet(*elements), result)

    @repeat(REPEAT_TIMES)
    def test_ordered_set_if_not_set_fail(self):
        elements = test_utils.random_collections(random.randint(0, 5))

        result = OrderedSet.ensure_set({iterables.flatten(elements, lazy=True)})
        self.assertNotIsInstance(result, OrderedSet)

    @repeat(REPEAT_TIMES)
    def test_add(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))
        new_element = test_utils.random_elements()[0]
        s1 = OrderedSet(*elements)
        s1.add(new_element)

        if new_element not in expected_elements:
            expected_elements.append(new_element)

        self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test_add_many(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        new_elements = test_utils.random_collections(random.randint(0, 5))
        flatten_new_elements = test_utils.list_without_repetitions(iterables.flatten(*new_elements, lazy=True))

        s1 = OrderedSet(*elements)
        s1.add_many(flatten_new_elements)

        for new_element in flatten_new_elements:
            if new_element not in expected_elements:
                expected_elements.append(new_element)

        self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test_clear(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements)
        s1.clear()

        self.assertEqual([], list(s1))

    @repeat(REPEAT_TIMES)
    def test_copy(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements)
        s1_copy = s1.copy()

        self.assertEqual(s1, s1_copy)
        self.assertIsNot(s1, s1_copy)

    @repeat(REPEAT_TIMES)
    def test_discard(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))
        elements_to_delete = test_utils.random_elements()[0]
        s1 = OrderedSet(*elements)
        s1.discard(elements_to_delete)

        if elements_to_delete in expected_elements:
            expected_elements.remove(elements_to_delete)
            self.assertEqual(expected_elements, list(s1))
        else:
            self.assertEqual(expected_elements, list(s1))

        s1.discard({})  # TypeError not raised
        s1.discard(set())  # TypeError not raised
        s1.discard({1, 2, 3})  # TypeError not raised

    @repeat(REPEAT_TIMES)
    def test_discard_many(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        elements_to_delete = test_utils.random_collections(random.randint(0, 5))
        flatten_elements_to_delete = test_utils.list_without_repetitions(iterables.flatten(*elements_to_delete, lazy=True))

        s1 = OrderedSet(*elements)
        s1.discard_many(flatten_elements_to_delete)

        for new_element in flatten_elements_to_delete:
            if new_element in expected_elements:
                expected_elements.remove(new_element)

        self.assertEqual(expected_elements, list(s1))

        s1.discard({})  # TypeError not raised
        s1.discard(set())  # TypeError not raised
        s1.discard({1, 2, 3})  # TypeError not raised

    @repeat(REPEAT_TIMES)
    def test_index(self):
        while not (
            elements := [element for element in test_utils.random_collections(random.randint(2, 15)) if element]
        ):
            pass
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))
        s1 = OrderedSet(*elements)

        start, stop, _ = self._random_start_stop_step(expected_elements)

        for i in range(random.randint(1, 20)):
            with self.subTest(i=i):
                try:
                    element = random.choice(expected_elements)
                except IndexError:
                    continue

                if element:
                    limits = []
                    if start is not None:
                        limits.append(max(0, start))
                        if stop is not None:
                            limits.append(stop)
                    try:
                        self.assertEqual(expected_elements.index(element, *limits), s1.index(element, *limits))
                    except ValueError:
                        self.assertRaises(ValueError, s1.index, element, *limits, raise_exception=True)

    @repeat(REPEAT_TIMES)
    def test_insert(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        s1 = OrderedSet(*elements)

        for i in range(random.randint(1, 20)):
            with self.subTest(i=i):
                index = random.randint(-50, 50)
                element = test_utils.random_elements()[0]
                if element in s1:
                    continue
                expected_elements.insert(index, element)
                s1.insert(index, element)
                self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test_is_disjoint(self):
        python_s1, s1 = self._create_set_and_ordered_set()
        python_s2, s2 = self._create_set_and_ordered_set()

        self.assertEqual(python_s1.isdisjoint(python_s2), s1.is_disjoint(s2))

    @repeat(REPEAT_TIMES)
    def test_is_subset(self):
        python_s1, s1 = self._create_set_and_ordered_set()
        python_s2, s2 = self._create_set_and_ordered_set()

        self.assertEqual(python_s1.issubset(python_s2), s1.is_subset(s2))
        self.assertEqual(python_s1 <= python_s2, s1 <= s2)

    @repeat(REPEAT_TIMES)
    def test_is_superset(self):
        python_s1, s1 = self._create_set_and_ordered_set()
        python_s2, s2 = self._create_set_and_ordered_set()

        self.assertEqual(python_s1.issuperset(python_s2), s1.is_superset(s2))
        self.assertEqual(python_s1 >= python_s2, s1 >= s2)

    @repeat(REPEAT_TIMES)
    def test_pop(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        flatten_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))
        s1 = OrderedSet(*elements)

        for i in range(-len(flatten_elements), len(flatten_elements)):
            with self.subTest(i=i):
                flatten_elements_copy = flatten_elements.copy()
                s1_copy = s1.copy()
                self.assertEqual(flatten_elements_copy.pop(i), s1_copy.pop(i))
                self.assertEqual(flatten_elements_copy, list(s1_copy))

        self._index_access_exceptions(s1, s1.pop)

    @repeat(REPEAT_TIMES)
    def test_reverse(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        s1 = OrderedSet(*elements)

        expected_elements.reverse()
        s1.reverse()

        self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test_sort(self):
        elements = test_utils.random_collections(random.randint(0, 5))
        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements, lazy=True))

        s1 = OrderedSet(*elements)

        try:
            expected_elements.sort()
            s1.sort()
            self.assertEqual(expected_elements, list(s1))
        except TypeError:
            self.assertRaises(TypeError, s1.sort)

        try:
            expected_elements.sort(reverse=True)
            s1.sort(reverse=True)
            self.assertEqual(expected_elements, list(s1))
        except TypeError:
            self.assertRaises(TypeError, s1.sort, reverse=True)

    @repeat(REPEAT_TIMES)
    def test_symmetric_difference_difference_update(self):
        elements_s1 = test_utils.random_collections(random.randint(0, 5))
        elements_s2 = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements_s1)
        s2 = OrderedSet(*elements_s2)

        flatten_elements_s1 = test_utils.list_without_repetitions(iterables.flatten(*elements_s1, lazy=True))
        flatten_elements_s2 = test_utils.list_without_repetitions(iterables.flatten(*elements_s2, lazy=True))
        fs1_minus_fs2 = [element_s1 for element_s1 in flatten_elements_s1 if element_s1 not in flatten_elements_s2]
        fs2_minus_fs1 = [element_s2 for element_s2 in flatten_elements_s2 if element_s2 not in flatten_elements_s1]
        expected_elements = fs1_minus_fs2 + fs2_minus_fs1

        self.assertEqual(expected_elements, list(s1.symmetric_difference(s2)))

        s1.symmetric_difference_update(s2)
        self.assertEqual(expected_elements, list(s1))

    @repeat(REPEAT_TIMES)
    def test_union_union_update_update(self):
        elements_s1 = test_utils.random_collections(random.randint(0, 5))
        elements_s2 = test_utils.random_collections(random.randint(0, 5))
        s1 = OrderedSet(*elements_s1)
        s2 = OrderedSet(*elements_s2)

        expected_elements = test_utils.list_without_repetitions(iterables.flatten(*elements_s1 + elements_s2, lazy=True))

        self.assertEqual(expected_elements, list(s1.union(s2)))

        s1.union_update(s2)
        self.assertEqual(expected_elements, list(s1))

        s1 = OrderedSet(*elements_s1)
        s1.update(s2)
        self.assertEqual(expected_elements, list(s1))

import datetime
import difflib
import json
import pathlib
import random
import re
import secrets
import string
import unicodedata
from typing import Iterable, Sequence, Type, overload

from flanautils import constants
from flanautils.models.ratio_match import RatioMatch


def cartesian_product_string_matching(a_text: str | Iterable[str], b_text: str | Iterable[str], min_ratio: float = 0) -> dict[dict[str, float]]:
    """
    Compare between all the strings of the first iterable with all of the second (cartesian product) and returns a
    dictionary with the scores.
    """

    a_words = a_text.split() if isinstance(a_text, str) else a_text
    b_words = b_text.split() if isinstance(b_text, str) else b_text
    return {a_word: matches for a_word in a_words if (matches := {b_word: ratio for b_word in b_words if (ratio := matching_ratio(a=a_word, b=b_word)) >= min_ratio})}


def find_jsons(text: str) -> list[dict]:
    """Find all well formatted JSONs in the text and return them in dictionaries."""

    text = path_to_text(text)

    jsons = []
    position = 0
    while (position := text.find('{', position)) != -1:
        result, position = json.JSONDecoder().raw_decode(text, position)
        jsons.append(result)
    return jsons


def find_environment_variables(text: str | pathlib.Path) -> dict:
    """Looks for environment variables in the text in .env format (key=value)."""

    # noinspection PyTypeChecker
    return dict(line.split('=', maxsplit=1) for line in path_to_text(text).splitlines() if '=' in line)


def join_last_separator(elements: Iterable, separator: str, last_separator: str, final_char='') -> str:
    """
    Join all the elements in a string, using a separator for all of them except the last one, where it uses
    last_separator.

    You can also add to final char.

    >>> join_last_separator(['Uno', 'dos', 'tres', 'cuatro'], ', ', ' y ', '.')
    'Uno, dos, tres y cuatro.'
    """

    elements = list(elements)
    if not len(elements):
        return ''
    if len(elements) == 1:
        return f'{elements[0]}{final_char}'
    return f'{separator.join(elements[:-1])}{last_separator}{elements[-1]}{final_char}'


def matching_ratio(a: Sequence[str], b: Sequence[str], original_index_weight=0.8, custom_index_weight=0.2) -> float:
    """
    Compare two sequences and return the score.

    It is made up of two different indices. The first uses difflib.SequenceMatcher and the second, a custom one that
    obtains a ratio of equal elements over the total number of elements.

    The weights of both indices can be configured by arguments.
    """

    if custom_index_weight > 0:
        match_count = 0
        i = None
        for i, (a_element, b_element) in enumerate(zip(a, b), start=1):
            if a_element == b_element:
                match_count += 1
        custom_matching_ratio = match_count / i if i else 0.5
    else:
        custom_matching_ratio = 0

    return original_index_weight * difflib.SequenceMatcher(a=a, b=b).ratio() + custom_index_weight * custom_matching_ratio


def numbers_to_words(number: int, language='es') -> str:
    """
    Convert an integer into its textual representation according to the language.

    >>> numbers_to_words(7)
    'siete'
    >>> numbers_to_words(92)
    'noventa y dos'
    >>> numbers_to_words(15)
    'quince'
    >>> numbers_to_words(16)
    'dieciséis'
    """

    if number >= 0:
        is_positive = True
    else:
        is_positive = False
        number *= -1

    if number not in range(0, 101):
        raise ValueError('value out of range')

    if language == 'es':
        number_word_es = constants.NUMBER_WORDS[language]
        try:
            result = number_word_es[number]
        except KeyError:
            tens, units = divmod(number, 10)
            separator = ''
            if tens == 1:
                tens_word = 'dieci'
            elif tens == 2:
                tens_word = 'veinti'
            elif tens == 10:
                tens_word = 'ciento'
            else:
                separator = ' y '
                tens_word = number_word_es[number - units]
            result = f"{tens_word}{separator}{number_word_es[units]}"
        if is_positive:
            return result
        else:
            return f"{number_word_es['-']} {result}"
    else:
        raise NotImplementedError('not implemented for that language')


def path_to_text(path: str | pathlib.Path) -> str:
    """
    Returns the content of the file as text.

    Returns the path argument as is if path is not a valid path string or pathlib.Path.
    """

    return read_file(path) or path


@overload
def random_string(min_len: int, max_len: int, letters=True, numbers=True, n_spaces=0) -> str:
    pass


@overload
def random_string(str_len=10, letters=True, numbers=True, n_spaces=0) -> str:
    pass


def random_string(min_len=10, max_len=None, letters=True, numbers=True, n_spaces=0) -> str:
    """
    Generate a random string.

    It can generate random strings of random size within the limits specified by arguments.

    You can specify the content of the strings: letters, numbers and number of spaces.
    """

    if isinstance(min_len, bool):
        letters = min_len
        min_len = None
        if isinstance(max_len, bool):
            numbers = max_len
            max_len = None
    elif isinstance(max_len, bool):
        letters = max_len
        max_len = None
    characters = f"{string.ascii_letters if letters else ''}{string.digits if numbers else ''}{' ' * n_spaces}"

    if max_len is not None:
        if max_len < min_len:
            return ''
        min_len = random.randint(min_len, max_len)

    return ''.join(secrets.choice(characters) for _ in range(min_len))


def read_file(path: str | pathlib.Path) -> str | None:
    """
    Returns the content of the file as text.

    Returns None if path is not a valid path string or pathlib.Path.
    """

    match path:
        case str() | pathlib.Path() as path:
            if pathlib.Path(path).is_file():
                with open(path) as file:
                    return file.read()


def remove_accents(text: str, ignore=('ñ', 'ç')) -> str:
    """
    Encode the string to remove the accents from non ascii characters.

    Ignore the strings contained in ignore argument. By default ignore=('ñ', 'ç').

    >>> remove_accents('aáeèiîoöuuºªçñ')
    'aaeeiioouuçñ'
    >>> remove_accents('Mañana iba a salir pero el otro día iba por la calle y casi me atropella un camión que iba muy rapido.')
    'Mañana iba a salir pero el otro dia iba por la calle y casi me atropella un camion que iba muy rapido.'
    """

    return ''.join(char if char in ignore else unicodedata.normalize('NFD', char).encode('ascii', 'ignore').decode() for char in text)


@overload
def str_to_class(class_names: str | Type, globals_: dict) -> Type:
    pass


@overload
def str_to_class(class_names: Iterable[str | Type], globals_: dict) -> tuple[Type, ...]:
    pass


def str_to_class(class_names: str | Type | Iterable[str | Type], globals_: dict) -> Type | tuple[Type, ...]:
    """Converts the class or classes names into Python Types found in globals_."""

    globals_ = globals_ or {}
    if isinstance(class_names, str):
        return globals_[class_names]
    else:
        return tuple(globals_[class_name] for class_name in class_names)


def sum_numbers_in_text(text: str, language='es') -> int:
    """
    Add all the existing numbers in a text, whether they are in numerical or textual form.

    >>> sum_numbers_in_text('Uno más dos. Y luego cuarenta y cuatro y cuarenta y 2 y 10 y 1 más 7.')
    107
    """

    words = translate(text, {symbol: None for symbol in constants.SYMBOLS}).split()
    n = 0
    for word in words:
        try:
            n += int(word)
        except ValueError:
            pass

    return n + words_to_numbers(text, language=language)


def translate(text: str, replacements: dict) -> str:
    """
    Returns a copy of text with the replacements applied.

    >>> translate('abc.-.', {'.': '*', '-': '<===>'})
    'abc*<===>*'
    >>> translate('Hola1 que2 ase3', {'Hola': 'Hi', 'que': 'ase', 'ase': None})
    'Hi1 ase2 3'
    """

    if not replacements:
        return text

    result: list[str] = []

    start = 0
    while start < len(text):
        pattern: list[str] = []

        for char in text[start:]:
            pattern.append(char)
            try:
                new_value = replacements[''.join(pattern)]
            except KeyError:
                pass
            else:
                result.append(new_value or '')
                start += len(pattern)
                break
        else:
            result.append(text[start])
            start += 1

    return ''.join(result)


def words_to_numbers(text: str, ignore_no_numbers=True, language='es') -> int:
    """
    Convert all numbers in textual representation, according to the language, into an integer and return the sum of
    them.

    >>> words_to_numbers('Borra veintidos mensajes. Y... luego borra otros treinta y cinco.')
    57
    """

    text = remove_accents(text)

    if language == 'es':
        number_words_es = constants.NUMBER_WORDS[language]
        text = re.sub(r'(([ei]nt[aeio])|(ec))', r'\1 ', text)
        text = translate(text, {symbol: None for symbol in constants.SYMBOLS} | {'y': ' '})
        words = text.lower().split()
        n = 0
        sign_ = 1
        for word in words:
            if matching_ratio(a=word, b=number_words_es['-']) >= constants.NUMBERS_RATIO_MATCHING:
                sign_ = -1
                continue

            word_possible_matches = []
            for number_word in number_words_es.values():
                ratio = matching_ratio(a=word, b=number_word)
                if ratio >= constants.NUMBERS_RATIO_MATCHING:
                    word_possible_matches.append(RatioMatch(number_words_es[number_word], ratio))

            if word_possible_matches:
                n += sign_ * max(word_possible_matches, key=lambda match: match.ratio).element
            elif not ignore_no_numbers:
                raise KeyError(word)

        return n

    raise NotImplementedError('not implemented for that language')


def words_to_time(text: str, language='es') -> datetime.timedelta:
    """
    Convert time in textual representation, according to the language, into a datetime.timedelta.

    >>> words_to_time('Un minuto y 10 segundos.')
    datetime.timedelta(seconds=70)
    """

    if language == 'es':
        delta_time = datetime.timedelta()
        n = 0
        for word in text.split():
            if matching_ratio(a=word, b='segundo') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(seconds=n)
                n = 0
            elif matching_ratio(a=word, b='minuto') >= constants.TIME_UNITS_RATIO_MATCHING or matching_ratio(a=word, b='min') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(minutes=n)
                n = 0
            elif matching_ratio(a=word, b='hora') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(hours=n)
                n = 0
            elif matching_ratio(a=word, b='dia') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(days=n)
                n = 0
            elif matching_ratio(a=word, b='semana') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(weeks=n)
                n = 0
            elif matching_ratio(a=word, b='mes') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(weeks=n * 4.34524)
                n = 0
            elif matching_ratio(a=word, b='año') >= constants.TIME_UNITS_RATIO_MATCHING:
                delta_time += datetime.timedelta(weeks=n * 52.1429)
                n = 0
            else:
                n += sum_numbers_in_text(word)

        return delta_time

    raise NotImplementedError('not implemented for that language')

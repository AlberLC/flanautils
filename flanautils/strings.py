import datetime
import json
import pathlib
import random
import re
import secrets
import string
from typing import Iterable, Type, overload

import jellyfish
import unicodedata

from flanautils import constants, iterables


def cartesian_product_string_matching(a_text: str | Iterable[str], b_text: str | Iterable[str], min_score: float = 0) -> dict[str, dict[str, float]]:
    """
    Compare between all the strings of the first iterable with all of the second (cartesian product) and returns a
    dictionary with the scores.
    """

    a_words = a_text.split() if isinstance(a_text, str) else a_text
    b_words = b_text.split() if isinstance(b_text, str) else b_text
    return {a_word: matches for a_word in a_words if (matches := {b_word: score for b_word in b_words if (score := jellyfish.jaro_winkler_similarity(a_word, b_word)) >= min_score})}


def cast_number(text: str, raise_exception=True) -> int | float | str:
    """
    Try to cast a string to a number.

    If raise_exception=False (True by default), returns the input as it is.
    """

    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            if raise_exception:
                raise
            else:
                return text


def find_coordinates(text: str) -> tuple[float, float] | list[tuple[float, float]] | None:
    """
    Find coordinates in string.

    - If one pair of numbers are matched, returns (latitude, longitude)
    - If more of one pair of numbers are matched, returns [(latitude, longitude), ...]
    - If not match, returns None

    >>> find_coordinates('holaaaa 85.1, 44.3515')
    (85.1, 44.3515)
    >>> find_coordinates('ey que pasa+654.1464;,;+ + +-456.4164hola')
    (654.1464, -456.4164)
    >>> find_coordinates('ey que pasa+654.1464;,;+ + -+456.4164hola    40+5.5')
    [(654.1464, 456.4164), (40.0, 5.5)]
    >>> find_coordinates('ey que pasa')

    """

    results = re.findall(r'[-+\d.]+[,;\s+-]+[-+\d.]+', replace(text, {'-': ' -', '+': ' +'}))

    formatted_results = []
    for result in results:
        try:
            words = re.split(r'[,;\s+]+', result)
            latitude, longitude = iterables.filter(words, condition=lambda e: isinstance(e, int | float), cast_numbers=True)
        except ValueError:
            continue
        formatted_results.append((float(latitude), float(longitude)))

    match formatted_results:
        case [single]:
            return single
        case [_, *_]:
            return formatted_results


def find_jsons(text: str | pathlib.Path) -> list[dict]:
    """Find all well formatted JSONs in a string or in a pathlib.Path and return them in dictionaries."""

    text = read_file(text) or text

    jsons = []
    position = 0
    while (position := text.find('{', position)) != -1:
        result, position = json.JSONDecoder().raw_decode(text, position)
        jsons.append(result)
    return jsons


def find_environment_variables(text: str | pathlib.Path) -> dict:
    """Looks for environment variables in a string or in a pathlib.Path in .env format (key=value)."""

    text = read_file(text) or text
    # noinspection PyTypeChecker
    return dict(line.split('=', maxsplit=1) for original_line in text.splitlines() if '=' in (line := original_line.strip()) and not line.startswith('#'))


def find_urls(text: str) -> list[str]:
    """Returns the substrings that match the url pattern."""

    return re.findall('(?:http|www\.)[-a-zA-Z0-9()@:%_+.~#?&/=]+', text)


def find_url_domains(text: str) -> list[str]:
    """Returns the substrings that match the url domain pattern."""

    return re.findall('(?:http.+?/|www\.|@)([\w.]+)(?!.*@)', text)


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


def numbers_to_text(number: int, language='es') -> str:
    """
    Convert an integer into its textual representation.

    >>> numbers_to_text(7)
    'siete'
    >>> numbers_to_text(92)
    'noventa y dos'
    >>> numbers_to_text(15)
    'quince'
    >>> numbers_to_text(16)
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


def remove_accents(text: str, ignore: Iterable = ('ñ', 'ç')) -> str:
    """
    Removes the accents from the string.

    Ignore the characters contained in ignore argument. By default ignore=('ñ', 'ç').

    >>> remove_accents('aáeèiîoöuuºªçñ')
    'aaeeiioouuºªçñ'
    >>> remove_accents('👉🏻Mañana iba a salir pero el otro día iba por la calle y casi me atropella un camión 🚛 que iba muy rápido.')
    '👉🏻Mañana iba a salir pero el otro dia iba por la calle y casi me atropella un camion 🚛 que iba muy rapido.'
    """

    def remove_accents_generator():
        for char in text:
            if char in ignore:
                yield char
            else:
                normalize_chars = unicodedata.normalize('NFD', char)
                for normalize_char in normalize_chars:
                    if unicodedata.category(normalize_char) != 'Mn':
                        yield normalize_char

    return ''.join(remove_accents_generator())


def remove_symbols(text: str, ignore: Iterable = (), replace_with='') -> str:
    """
    Remove the typical symbols from the string.

    Ignore the characters contained in ignore argument. By default ignore=().

    Symbols are replaced with replace_with argument. By default replace_with=''.

    >>> remove_symbols('¿No vás muy rápido? Yo creo que sí.')
    'No vás muy rápido Yo creo que sí'
    >>> remove_symbols('¿No vás muy rápido? Yo creo que sí.', ignore=('?',), replace_with='8')
    '8No vás muy rápido? Yo creo que sí8'
    """

    return ''.join((char if char in ignore else replace_with) if char in constants.SYMBOLS else char for char in text)


replace_symbols = remove_symbols


def replace(text: str, replacements: dict) -> str:
    """
    Returns a copy of text with the replacements applied.

    >>> replace('abc.-.', {'.': '*', '-': '<===>'})
    'abc*<===>*'
    >>> replace('Hola1 que2 ase3', {'Hola': 'Hi', 'que': 'ase', 'ase': None})
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


translate = replace


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


def text_to_number(text: str, ignore_no_numbers=True, language='es') -> int | float:
    """
    Convert numbers from text to numeric and return the sum of them.

    >>> text_to_number('cientocincuentaydos')
    152
    >>> text_to_number('Borra veintidos mensajes. Y... luego borra otros treinta y cinco.')
    57
    >>> text_to_number('uno menos dos menos tres')
    -4
    >>> text_to_number('uno - dos y tres')
    -4
    >>> text_to_number('uno menos dos mas tres')
    2
    >>> text_to_number('uno - dos mas tres')
    2
    >>> text_to_number('uno - dos + tres')
    2
    >>> text_to_number('Uno más dos. Y luego cuarenta y cuatro y cuarenta y 2 y 10 y 1 más 7.')
    107
    >>> text_to_number('0.1 + uno más dos, 5.2 -1.1 mas 5.3 -5.8 ')
    6.7
    """

    text = remove_accents(text)
    text = remove_symbols(text, ('+', '-', '.'))

    if language == 'es':
        number_words_es = constants.NUMBER_WORDS[language]
        text = replace(text, {'y': ' ', 'ç': None})
        text = re.sub(r'(([ei]nt[aeio])|(ec))', r'\1 ', text)
        words = text.lower().split()
        n = 0
        sign = 1
        for word in words:
            word = word.strip('.')
            try:
                n += sign * cast_number(word)
            except ValueError:
                pass
            else:
                continue

            if len(word) > constants.TEXT_TO_NUMBER_MAX_WORD_LENGTH:
                continue

            if word == '+' or jellyfish.jaro_winkler_similarity(word, number_words_es['+']) >= constants.NUMBERS_SCORE_MATCHING:
                sign = 1
                continue
            elif word == '-' or jellyfish.jaro_winkler_similarity(word, number_words_es['-']) >= constants.NUMBERS_SCORE_MATCHING:
                sign = -1
                continue

            if word_matches := cartesian_product_string_matching(word, number_words_es.values(), constants.NUMBERS_SCORE_MATCHING):
                number_word = max(word_matches[word].items(), key=lambda item: item[1])[0]
                n += sign * number_words_es[number_word]
            elif not ignore_no_numbers:
                raise KeyError(word)

        return n

    raise NotImplementedError('not implemented for that language')


def text_to_time(text: str | Iterable[str], language='es') -> datetime.timedelta:
    """
    Convert time in textual representation into a datetime.timedelta.

    >>> text_to_time('Un minuto y 10 segundos.')
    datetime.timedelta(seconds=70)
    """

    if isinstance(text, str):
        words = text.split()
    else:
        words = text

    delta_time = datetime.timedelta()
    n = 0

    if language == 'es':
        for word in words:
            if jellyfish.jaro_winkler_similarity(word, 'segundo') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(seconds=n)
                n = 0
            elif jellyfish.jaro_winkler_similarity(word, 'minuto') >= constants.TIME_UNITS_SCORE_MATCHING or jellyfish.jaro_winkler_similarity(word, 'min') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(minutes=n)
                n = 0
            elif jellyfish.jaro_winkler_similarity(word, 'hora') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(hours=n)
                n = 0
            elif jellyfish.jaro_winkler_similarity(word, 'dia') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(days=n)
                n = 0
            elif jellyfish.jaro_winkler_similarity(word, 'semana') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(weeks=n)
                n = 0
            elif jellyfish.jaro_winkler_similarity(word, 'mes') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(weeks=n * constants.WEEKS_IN_A_MONTH)
                n = 0
            elif jellyfish.jaro_winkler_similarity(word, 'año') >= constants.TIME_UNITS_SCORE_MATCHING:
                delta_time += datetime.timedelta(weeks=n * constants.WEEKS_IN_A_YEAR)
                n = 0
            else:
                n += text_to_number(word)

        return delta_time

    raise NotImplementedError('not implemented for that language')

import contextlib
import os
import pathlib
import pkgutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import overload

from flanautils import strings


def find_paths_by_stem(
    stem: str,
    directory: str | pathlib.Path = '',
    lazy=False
) -> Iterator[pathlib.Path] | list[pathlib.Path]:
    """
    Returns the pathlib.Path objects of the directory that have the stem.

    If lazy=False (the default) it returns a list, if lazy=True, returns a generator.
    """

    generator_ = (path for path in pathlib.Path(directory).iterdir() if str(path).split('.', maxsplit=1)[0] == stem)
    return generator_ if lazy else list(generator_)


@overload
def next_path(path_template: str, start=1, exhaustive=True) -> str:
    pass


@overload
def next_path(path_template: pathlib.Path, start=1, exhaustive=True) -> pathlib.Path:
    pass


def next_path(path_template: str | pathlib.Path, start=1, exhaustive=True) -> str | pathlib.Path:
    """
    Finds the next free path in a sequentially named files.

    path_template has to follow the syntax of str.format().

    If exhaustive=True (the default) the function will take into account the gaps and ensure the lowest available index.
    If not, it will use a more efficient algorithm to find a free index, but it will not necessarily be the lowest
    possible.

    >>> pathlib.Path('file_1.txt').touch()
    >>> pathlib.Path('file_2.txt').touch()
    >>> pathlib.Path('file_4.txt').touch()

    >>> next_path('file_{}.txt')
    'file_3.txt'
    >>> next_path('file_{}.txt', exhaustive=False)
    'file_5.txt'

    >>> pathlib.Path('file_1.txt').unlink()
    >>> pathlib.Path('file_2.txt').unlink()
    >>> pathlib.Path('file_4.txt').unlink()
    """

    b = start

    if exhaustive:
        while pathlib.Path(path_template.format(b)).exists():
            b += 1
    else:
        while pathlib.Path(path_template.format(b)).exists():
            b *= 2
        a, b = (b // 2, b)
        while a + 1 < b:
            c = (a + b) // 2
            a, b = (c, b) if pathlib.Path(path_template.format(c)).exists() else (a, c)

    return path_template.format(b)


def resolve_path(path: str) -> pathlib.Path:
    """Resolves actual file or directory paths in distributed libraries."""

    path = path.strip('/')
    try:
        path, file = path.rsplit('/', 1)
    except ValueError:
        file = ''
    path = path.replace('/', '.')

    return pathlib.Path(pkgutil.resolve_name(path).__path__[0]) / file


def set_windows_environment_variables(variables: str | dict | pathlib.Path, search_jsons=True, set_in_system=False):
    """
    Set environment variables for Windows.

    If variables is a str or a pathlib.Path it looks for environment variables in that file in .env or json format.
    """

    match variables:
        case str() | pathlib.Path() as text:
            if pathlib.Path(text).is_file():
                with open(text) as file:
                    text = file.read()

            variables = {}
            if search_jsons:
                variables = {k: v for dict_ in strings.find_jsons(text) for k, v in dict_.items()}
            if not variables:
                variables = strings.find_environment_variables(text)
        case dict(variables):
            pass
        case _:
            raise TypeError('bad arguments')

    if set_in_system:
        for k, v in variables.items():
            subprocess.run(f'setx /m {k} {v}')
    else:
        for k, v in variables.items():
            os.environ[k] = v


@contextmanager
def suppress_low_level_stderr():
    """A context manager that redirects low level stderr to devnull."""

    with open(os.devnull, 'w') as err_null_file:
        stderr_fileno = sys.stderr.fileno()
        old_stderr_fileno = os.dup(sys.stderr.fileno())
        old_stderr = sys.stderr

        os.dup2(err_null_file.fileno(), stderr_fileno)
        sys.stderr = err_null_file

        try:
            yield
        finally:
            sys.stderr = old_stderr
            os.dup2(old_stderr_fileno, stderr_fileno)

            os.close(old_stderr_fileno)


@contextmanager
def suppress_low_level_stdout():
    """A context manager that redirects low level stdout to devnull."""

    with open(os.devnull, 'w') as out_null_file:
        stdout_fileno = sys.stdout.fileno()
        old_stdout_fileno = os.dup(sys.stdout.fileno())
        old_stdout = sys.stdout

        os.dup2(out_null_file.fileno(), stdout_fileno)
        sys.stdout = out_null_file

        try:
            yield
        finally:
            sys.stdout = old_stdout
            os.dup2(old_stdout_fileno, stdout_fileno)

            os.close(old_stdout_fileno)


@contextmanager
def suppress_stderr():
    """A context manager that redirects stderr to devnull."""

    with open(os.devnull, 'w') as null_file, contextlib.redirect_stderr(null_file):
        yield


@contextmanager
def suppress_stdout():
    """A context manager that redirects stdout to devnull."""

    with open(os.devnull, 'w') as null_file, contextlib.redirect_stdout(null_file):
        yield

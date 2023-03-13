import contextlib
import os
import pathlib
import pkgutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager

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

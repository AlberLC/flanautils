import contextlib
import os
import pathlib
import pkgutil
import subprocess
from contextlib import contextmanager

from flanautils import strings


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
def suppress_stderr():
    """A context manager that redirects stderr to devnull."""

    with open(os.devnull, 'w') as fnull:
        with contextlib.redirect_stderr(fnull) as err:
            yield err


@contextmanager
def suppress_stdout():
    """A context manager that redirects stdout to devnull."""

    with open(os.devnull, 'w') as fnull:
        with contextlib.redirect_stdout(fnull) as out:
            yield out

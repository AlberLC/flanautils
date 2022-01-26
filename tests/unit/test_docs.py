import doctest
import pathlib


def load_tests(_loader, tests, _ignore):
    path_names = [path.with_suffix('').as_posix().replace('.', '').replace('/', '.').strip('.') for path in pathlib.Path('..').glob(f'*[!venv]*/**/*.py')]
    for path_name in path_names:
        tests.addTests(doctest.DocTestSuite(path_name))
    return tests

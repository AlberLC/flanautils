import pathlib
import pkgutil

RESOURCES_ABSOLUTE_PATH = pathlib.Path(pkgutil.resolve_name(__name__).__path__[0])

plotly_es_url = RESOURCES_ABSOLUTE_PATH / 'plotly_es.js'

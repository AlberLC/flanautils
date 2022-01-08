import pathlib
import pkgutil

plotly_es_data = pkgutil.get_data(__package__, 'plotly_es.js')
plotly_es_url = pathlib.Path(__package__).resolve() / 'plotly_es.js'

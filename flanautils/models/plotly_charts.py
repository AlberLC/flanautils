from __future__ import annotations  # todo0 remove in 3.11

import functools
import pickle
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

import plotly
import plotly.basedatatypes
import plotly.graph_objects
import sympy
# noinspection PyProtectedMember
from plotly.io import _html, _kaleido

from flanautils import iterables, oss
from flanautils.models.bases import FlanaBase, MongoBase


def get_plotlyjs():
    """Hardcode a version of plotly in Spanish to render html."""

    with open(oss.resolve_path('flanautils/resources/plotly_es.js')) as f:
        return f.read()


_kaleido.scope.plotlyjs = oss.resolve_path('flanautils/resources/plotly_es.js')  # render image
_html.get_plotlyjs = get_plotlyjs  # render html


def find_resolution(func: Callable = None) -> Callable:
    """Decorator that gives the decorated function the image resolution."""

    @functools.wraps(func)
    def wrapper(self: MultiTraceChart, *args, **kwargs):
        if 'width' not in kwargs:
            kwargs['width'] = self.resolution[0]
        if 'height' not in kwargs:
            kwargs['height'] = self.resolution[1]
        if 'resolution' in kwargs:
            kwargs['width'] = kwargs['resolution'][0]
            kwargs['height'] = kwargs['resolution'][1]
            del kwargs['resolution']
        if 'size' in kwargs:
            kwargs['width'] = kwargs['size'][0]
            kwargs['height'] = kwargs['size'][1]
            del kwargs['size']

        return func(self, *args, **kwargs)

    return wrapper


@dataclass(unsafe_hash=True)
class TraceMetadata(FlanaBase):
    """Specifies the settings for a trace of a Plotly chart."""

    type_: plotly.basedatatypes = plotly.graph_objects.Scatter
    name: str = 'trace'
    group: str = None
    legend: str = 'trace'
    show: bool = True
    show_legend: bool = True
    show_markers: bool = False
    show_lines: bool = True
    color: str = 'black'
    opacity: float = 1
    pattern: dict = field(default_factory=dict)
    connect_gaps: bool = True
    default_x_data: float = None
    default_y_data: float = None
    default_min: str | float = 0
    default_max: str | float = 100
    y_tick_suffix: str = ''
    y_delta_tick: float = 10
    hide_y_ticks_if: str = 'False'
    x_data_multiplier: float = 1
    y_data_multiplier: float = 1
    y_axis_width: float = 120


@dataclass(unsafe_hash=True)
class MultiTraceChart(MongoBase, FlanaBase):
    """Class that simplifies the use of Plotly charts with several traces."""

    _font: dict = field(default_factory=dict)
    _legend: dict = field(default_factory=dict)
    _margin: dict = field(default_factory=dict)
    _title: dict = field(default_factory=dict)
    figure: plotly.graph_objects.Figure = field(default_factory=plotly.graph_objects.Figure)
    trace_metadatas: dict[str, TraceMetadata] = ()
    x_data: list = field(default_factory=list)
    all_y_data: list[list] = field(default_factory=list)
    show_middle_horizontal_line: bool = False
    resolution: tuple[int, int] = (1920, 1080)  # 3840×2160, 2560×1440, 2048×1152, 1920×1080, 1366×768, 1280×720, 850×480
    nbinsx: int = None

    def __post_init__(self):
        self.font = self._font
        self.legend = self._legend
        self.margin = self._margin
        self.title = self._title

    def __getattr__(self, item):
        if any(item.startswith(start) for start in ('xaxis', 'yaxis')):
            return vars(self)[item]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if not any(key.startswith(start) for start in ('xaxis', 'yaxis')):
            super().__setattr__(key, value)
            return

        key_name = key[:5]
        try:
            axis_index = int(key[5:])
        except ValueError:
            axis_index = 1
        key = f'{key_name}{axis_index}'

        try:
            vars(self)[key] |= value
        except KeyError:
            super().__setattr__(key, value)
        self.figure.update_layout({key: value})

    def _mongo_repr(self) -> Any:
        return pickle.dumps(self)

    def add_lines(self):
        """Print the x-axis horizontal line."""

        if self.show_middle_horizontal_line:
            self.figure.add_shape(type='line', x0=0, x1=1, y0=0.5, y1=0.5, xref='paper', yref='paper', line_width=1, line_dash='dot')

    def clear(self):
        """Reinitialize the object."""

        self.figure = plotly.graph_objects.Figure()
        for attribute_name in vars(self):
            if any(attribute_name.startswith(start) for start in ('xaxis', 'yaxis')):
                super().__setattr__(attribute_name, {})

        self.__post_init__()

    def draw(self):
        """Apply the trace metadata and the axis data to draw them in the Plotly figure."""

        self.add_lines()

        active_trace_groups = set()
        axis_index = 1
        tick_len = 0
        for trace_metadata, y_data in zip(self.trace_metadatas.values(), self.all_y_data):
            if not trace_metadata.show:
                continue

            show_y_axis = not trace_metadata.group or trace_metadata.group not in active_trace_groups
            active_trace_groups.add(trace_metadata.group)
            self.format_trace(trace_metadata, y_data, axis_index, tick_len, show_y_axis)
            axis_index += 1
            if show_y_axis:
                tick_len += trace_metadata.y_axis_width

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, kwargs: dict):
        self._font |= kwargs
        self.figure.update_layout({'font': self._font})

    def format_trace(self, trace_metadata: TraceMetadata, y_data: Iterable, axis_index: int, tick_len: float, show_y_axis=True):
        """Apply the trace metadata and the axis data to format and draw one trace in the Plotly figure."""

        def adjust_y_axis_height():
            y_data_ = [y_datum for y_datum in y_data if y_datum is not None]

            try:
                min_y_data = min(y_data_)
            except ValueError:
                min_y_data = trace_metadata.default_min
            try:
                max_y_data = max(y_data_)
            except ValueError:
                max_y_data = trace_metadata.default_max

            if isinstance(trace_metadata.default_min, str):
                default_min = float(sympy.sympify(trace_metadata.default_min.format(min_y_data=min_y_data, max_y_data=max_y_data)))
            else:
                default_min = trace_metadata.default_min

            if isinstance(trace_metadata.default_max, str):
                default_max = float(sympy.sympify(trace_metadata.default_max.format(min_y_data=min_y_data, max_y_data=max_y_data)))
            else:
                default_max = trace_metadata.default_max

            min_delta = default_min - min_y_data
            max_delta = max_y_data - default_max
            if min_delta > 0 or max_delta > 0:
                delta = max(min_delta, max_delta)
            else:
                delta = 0
            if delta:
                min_tick = round(default_min - delta - 5, -1)
                max_tick = round(default_max + delta + 5, -1)
            else:
                min_tick = default_min - delta
                max_tick = default_max + delta

            setattr(self, f'yaxis{axis_index}', {'range': (min_tick, max_tick)})

            # ----- Hide ticks -----
            tick_vals = []
            for tick in iterables.frange(min_tick, max_tick, trace_metadata.y_delta_tick, include_last=True):
                if sympy.sympify(trace_metadata.hide_y_ticks_if.format(tick=(tick_ := round(tick, 2)), min_y_data=min_y_data, max_y_data=max_y_data)):
                    tick_vals.append(None)
                else:
                    tick_vals.append(tick_)

            setattr(self, f'yaxis{axis_index}', {'tickvals': tick_vals})

        # ----- Update the data -----
        x_data = self.update_data(self.x_data, trace_metadata.default_x_data, trace_metadata.x_data_multiplier)
        y_data = self.update_data(y_data, trace_metadata.default_y_data, trace_metadata.y_data_multiplier)

        match trace_metadata.show_lines, trace_metadata.show_markers:
            case [True, True]:
                mode = 'lines+markers'
            case [True, False]:
                mode = 'lines'
            case [False, True]:
                mode = 'markers'
            case _:
                mode = None

        if issubclass(trace_metadata.type_, plotly.graph_objects.Scatter):
            extra_trace_kwargs = {
                'mode': mode,
                'line': {'color': trace_metadata.color},
                'connectgaps': trace_metadata.connect_gaps
            }
        else:
            extra_trace_kwargs = {
                'marker': {'color': trace_metadata.color, 'pattern': trace_metadata.pattern},
                'histfunc': 'sum',
                'xbins': {'size': 60 * 60 * 1000}
            }

        trace = trace_metadata.type_(
            x=x_data,
            y=y_data,
            yaxis=f'y{axis_index}',
            name=trace_metadata.legend,
            showlegend=trace_metadata.show_legend,
            opacity=trace_metadata.opacity,
            **extra_trace_kwargs
        )

        # ----- Base kwargs -----
        setattr(self, f'yaxis{axis_index}', {
            'ticks': 'outside',
            'ticklen': tick_len,
            'color': 'rgba(0,0,0,0)',
            'tickfont_color': trace_metadata.color,
            'ticksuffix': trace_metadata.y_tick_suffix,
            'dtick': trace_metadata.y_delta_tick,
            'showticklabels': show_y_axis
        })

        # ----- Overlaying -----
        if axis_index != 1:
            setattr(self, f'yaxis{axis_index}', {'overlaying': 'y'})

        adjust_y_axis_height()

        self.figure.add_trace(trace)

    @property
    def legend(self):
        return self._legend

    @legend.setter
    def legend(self, kwargs: dict):
        self._legend |= kwargs
        self.figure.update_layout({'legend': self._legend})

    @property
    def margin(self):
        return self._margin

    @margin.setter
    def margin(self, kwargs: dict):
        self._margin |= kwargs
        self.figure.update_layout({'margin': self._margin})

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, kwargs: dict):
        self._title |= kwargs
        self.figure.update_layout({'title': self._title})

    @find_resolution
    def show(self, *args, **kwargs):
        self.figure.show(*args, **kwargs)

    @find_resolution
    def to_image(self, *args, **kwargs) -> bytes:
        return self.figure.to_image(*args, **kwargs)

    @staticmethod
    def update_data(data: Iterable, default_value: float, multiplier: float) -> list:
        """Apply a multiplier or default value to each element of the iterable."""

        updated_data = []
        for datum in data:
            if datum is None:
                updated_data.append(default_value)
            else:
                try:
                    updated_data.append(datum * multiplier)
                except TypeError:
                    updated_data.append(datum)

        return updated_data


@dataclass(unsafe_hash=True)
class DateChart(MultiTraceChart):
    """Inherits MultiTraceChart to provide date-dependent state."""

    show_now_vertical_line: bool = True

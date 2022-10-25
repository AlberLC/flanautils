from __future__ import annotations  # todo0 remove when it's by default

import itertools
import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, overload

from flanautils import iterables
from flanautils.models.bases import FlanaBase
from flanautils.models.enums import MediaType, Source


@dataclass(unsafe_hash=True)
class Media(FlanaBase):
    url: str = None
    bytes_: bytes = None
    type_: MediaType = None
    extension: str = None
    source: Source = None
    title: str = None
    author: str = None
    album: str = None
    song_info: Media = None

    @overload
    def __init__(self, url: str | pathlib.Path = None, type_: MediaType = None, extension: str = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    @overload
    def __init__(self, bytes_: bytes = None, type_: MediaType = None, extension: str = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    @overload
    def __init__(self, url: str | pathlib.Path = None, bytes_: bytes = None, type_: MediaType = None, extension: str = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    @overload
    def __init__(self, bytes_: bytes = None, url: str | pathlib.Path = None, type_: MediaType = None, extension: str = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    def __init__(self, *args, **kwargs):
        main_ars = list(itertools.takewhile(lambda arg_: isinstance(arg_, str | bytes | pathlib.Path), args))
        self.url = iterables.find(main_ars, str | pathlib.Path)
        self.bytes_ = iterables.find(reversed(main_ars), bytes)

        rest_attributes_names = ('type_', 'extension', 'source', 'title', 'author', 'album', 'song_info')
        for attributes_name, arg in zip(rest_attributes_names, itertools.dropwhile(lambda arg_: isinstance(arg_, str | bytes), args)):
            setattr(self, attributes_name, arg)

        self.url = kwargs.get('url') or self.url
        if isinstance(self.url, pathlib.Path):
            self.url = str(self.url)
        self.bytes_ = kwargs.get('bytes_') or self.bytes_
        self.type_ = kwargs.get('type_') or self.type_
        self.extension = kwargs.get('extension') or self.extension
        if not self.extension:
            self.extension = self.type_.default_extension
        self.source = kwargs.get('source') or self.source
        self.title = kwargs.get('title') or self.title
        self.author = kwargs.get('author') or self.author
        self.album = kwargs.get('album') or self.album
        self.song_info = kwargs.get('song_info') or self.song_info

    def __bool__(self):
        return bool(self.content)

    def _json_repr(self) -> Any:
        return {k: v.name if isinstance(v, Enum) else v for k, v in super()._json_repr().items()}

    @property
    def content(self) -> str | bytes | None:
        return self.url or self.bytes_

    def is_audio(self) -> bool:
        return self.type_ is MediaType.AUDIO

    def is_gif(self) -> bool:
        return self.type_ is MediaType.GIF

    def is_image(self) -> bool:
        return self.type_ is MediaType.IMAGE

    def is_video(self) -> bool:
        return self.type_ is MediaType.VIDEO

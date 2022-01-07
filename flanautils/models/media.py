from __future__ import annotations  # todo0 remove in 3.11

from dataclasses import dataclass
from enum import Enum
from typing import Any, overload

from flanautils.models.bases import FlanaBase
from flanautils.models.enums import MediaType, Source


@dataclass(unsafe_hash=True)
class Media(FlanaBase):
    url: str = None
    bytes_: bytes = None
    type_: MediaType = None
    source: Source = None
    title: str = None
    author: str = None
    album: str = None
    song_info: Media = None

    @overload
    def __init__(self, url: str = None, type_: MediaType = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    @overload
    def __init__(self, bytes_: bytes = None, type_: MediaType = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    @overload
    def __init__(self, url: str = None, bytes_: bytes = None, type_: MediaType = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    @overload
    def __init__(self, bytes_: bytes = None, url: str = None, type_: MediaType = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None):
        pass

    def __init__(self, url: str = None, bytes_: bytes = None, type_: MediaType = None, source: Source = None, title: str = None, author: str = None, album: str = None, song_info: Media = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        match url, bytes_:
            case [bytes(bytes_), str(url)]:
                pass
            case [bytes(), bytes(bytes_)]:
                url = None
            case [str() | bytes(), MediaType()]:
                type_, source, title, author, album, song_info = bytes_, type_, source, title, author, album
                match url:
                    case str():
                        bytes_ = None
                    case bytes():
                        url, bytes_ = None, url

        self.url = url
        self.bytes_ = bytes_
        self.type_ = type_
        self.source = source
        self.title = title
        self.author = author
        self.album = album
        self.song_info = song_info

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

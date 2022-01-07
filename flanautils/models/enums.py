from enum import auto

from flanautils.models.bases import FlanaEnum


class MediaType(FlanaEnum):
    AUDIO = auto()
    ERROR = auto()
    GIF = auto()
    IMAGE = auto()
    VIDEO = auto()

    @property
    def extension(self) -> str:
        if self is MediaType.AUDIO:
            return 'mp3'
        elif self is MediaType.GIF:
            return 'gif'
        elif self is MediaType.IMAGE:
            return 'jpg'
        elif self is MediaType.VIDEO:
            return 'mp4'
        else:
            return ''


class Source(FlanaEnum):
    INSTAGRAM = auto()
    LOCAL = auto()
    TIKTOK = auto()
    TWITTER = auto()
    REDDIT = auto()
    YOUTUBE = auto()

    @property
    def name(self):
        if self is Source.INSTAGRAM:
            return 'Instagram'
        elif self is Source.TIKTOK:
            return 'TikTok'
        elif self is Source.TWITTER:
            return 'Twitter'
        elif self is Source.REDDIT:
            return 'Reddit'
        elif self is Source.YOUTUBE:
            return 'YouTube'

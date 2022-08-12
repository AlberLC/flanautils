import asyncio
import platform
import subprocess

from flanautils import asyncs
from flanautils.models.enums import MediaType
from flanautils.models.media import Media


async def mp4_to_gif(bytes_: bytes) -> bytes:
    """Convert video in mp4 format given in bytes into video in gif format using FFmpeg."""

    kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if platform.system() == 'Windows' else {}
    process = await asyncio.create_subprocess_shell(
        'ffmpeg -i pipe: -f gif -vf "fps=30,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 -y pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs
    )
    stdout, _ = await process.communicate(bytes_)

    return stdout


async def video_to_audio(media: Media, bitrate=192, sample_rate=44100, channels=2) -> Media:
    if media.type_ is not MediaType.VIDEO or not media.content:
        return media

    media = media.deep_copy()

    if not media.bytes_:
        media.bytes_ = await asyncs.get_request(media.url)

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', 'pipe:', '-b:a', f'{bitrate}k', '-ar', str(sample_rate), '-ac', str(channels), '-f', 'mp3', 'pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate(media.bytes_)
    media.bytes_ = stdout

    media.url = None
    media.type_ = MediaType.AUDIO
    media.extension = 'mp3'

    return media

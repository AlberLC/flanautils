import asyncio
import pathlib
import platform
import subprocess
import uuid
from collections import defaultdict

import flanautils


async def edit_metadata(bytes_: bytes, metadata: dict, overwrite=True) -> bytes:
    if (await get_metadata(bytes_))['title'] and not overwrite:
        return bytes_

    metadata_args = []
    for k, v in metadata.items():
        metadata_args.append('-metadata')
        metadata_args.append(f'{k}={v}')

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', 'pipe:', '-c', 'copy', *metadata_args, '-f', await get_format(bytes_), 'pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate(bytes_)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return stdout


async def get_format(bytes_: bytes) -> str:
    process = await asyncio.create_subprocess_exec(
        'ffprobe', '-show_format', 'pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate(bytes_)

    format_ = flanautils.find_environment_variables(stdout.decode())['format_name']
    return 'mp4' if 'mp4' in format_ else format_


async def get_metadata(bytes_: bytes) -> defaultdict:
    metadata_file_name = f'{str(uuid.uuid1())}.txt'
    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', 'pipe:', '-f', 'ffmetadata', metadata_file_name,
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    await process.communicate(bytes_)

    metadata = flanautils.find_environment_variables(metadata_file_name)
    pathlib.Path(metadata_file_name).unlink(missing_ok=True)

    return defaultdict(lambda: None, {k.lower(): v for k, v in metadata.items()})


async def to_gif(bytes_: bytes) -> bytes:
    """Convert video given in bytes into video in gif format using FFmpeg."""

    kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if platform.system() == 'Windows' else {}
    process = await asyncio.create_subprocess_shell(
        'ffmpeg -i pipe: -f gif -vf "fps=30,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs
    )
    stdout, _stderr = await process.communicate(bytes_)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return stdout


async def to_mp3(bytes_: bytes, bitrate=192, sample_rate=44100, channels=2) -> bytes:
    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', 'pipe:', '-b:a', f'{bitrate}k', '-ar', str(sample_rate), '-ac', str(channels), '-f', 'mp3', 'pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate(bytes_)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return stdout

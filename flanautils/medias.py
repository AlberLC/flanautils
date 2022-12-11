import asyncio
import platform
import subprocess

import flanautils


async def edit_metadata(bytes_: bytes, metadata: dict, overwrite=True) -> bytes:
    if not overwrite:
        old_metadata = await get_metadata(bytes_)
        metadata = {k: v for k, v in metadata.items() if k not in old_metadata}

    metadata_args = []
    for k, v in metadata.items():
        metadata_args.append('-metadata')
        metadata_args.append(f'{k}={v}')

    format_ = await get_format(bytes_)
    if 'mp4' in format_:
        format_ = 'mp4'

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', 'pipe:', '-c', 'copy', *metadata_args, '-f', format_, 'pipe:',
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

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return flanautils.find_environment_variables(stdout.decode())['format_name']


async def get_metadata(bytes_: bytes) -> dict:
    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', 'pipe:', '-f', 'ffmetadata', 'pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate(bytes_)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    metadata = flanautils.find_environment_variables(stdout.decode())

    return {k.lower(): v for k, v in metadata.items()}


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

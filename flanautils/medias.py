import asyncio
import pathlib
import uuid

import flanautils


async def edit_metadata(bytes_: bytes, metadata: dict, overwrite=True) -> bytes:
    """Edits the metadata of media file bytes."""

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
    """Gets the format of media file bytes."""

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
    """Gets the metadata dictionary of the media file bytes."""

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


# noinspection PyUnboundLocalVariable
async def merge(
    input_file_1: bytes | str | pathlib.Path,
    input_file_2: bytes | str | pathlib.Path = None,
    output_file: str | pathlib.Path = None,
    default_format='mp4'
) -> bytes | None:
    """
    Merges the input files into one.

    If output_file is not provided returns a default_format file bytes.
    """

    if isinstance(input_file_1, bytes):
        input_file_name_1 = str(uuid.uuid1())
        input_file_path_1 = pathlib.Path(input_file_name_1)
        input_file_path_1.write_bytes(input_file_1)
    else:
        input_file_name_1 = str(input_file_1)

    if input_file_2:
        if isinstance(input_file_2, bytes):
            input_file_name_2 = str(uuid.uuid1())
            input_file_path_2 = pathlib.Path(input_file_name_2)
            input_file_path_2.write_bytes(input_file_2)
        else:
            input_file_name_2 = str(input_file_2)
        input_2_args = ('-i', input_file_name_2)
    else:
        input_2_args = ()

    if output_file:
        output_file_name = str(output_file)
    else:
        output_file_name = f'{str(uuid.uuid1())}.{default_format}'
        output_file_path = pathlib.Path(output_file_name)
        output_file_path.touch()

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', input_file_name_1, *input_2_args, '-y', '-c', 'copy', output_file_name,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await process.wait()

    if isinstance(input_file_1, bytes):
        input_file_path_1.unlink(missing_ok=True)
    if isinstance(input_file_2, bytes):
        input_file_path_2.unlink(missing_ok=True)
    if not output_file:
        bytes_ = output_file_path.read_bytes()
        output_file_path.unlink(missing_ok=True)
        return bytes_


async def to_gif(bytes_: bytes) -> bytes:
    """Convert video given in bytes into video in gif format."""

    process = await asyncio.create_subprocess_shell(
        'ffmpeg -i pipe: -f gif -vf "fps=30,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 pipe:',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate(bytes_)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return stdout


async def to_mp3(bytes_: bytes, bitrate=192, sample_rate=44100, channels=2) -> bytes:
    """Extract and return audio in mp3 format from the media file bytes."""

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

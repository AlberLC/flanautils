import asyncio
import pathlib
import uuid

import flanautils


async def edit_metadata(input_file: bytes | str | pathlib.Path, metadata: dict, overwrite=True) -> bytes:
    """Edits the media file metadata."""

    if not overwrite:
        old_metadata = await get_metadata(input_file)
        metadata = {k: v for k, v in metadata.items() if k not in old_metadata}
    if not metadata:
        if isinstance(input_file, bytes):
            return input_file
        else:
            return pathlib.Path(input_file).read_bytes()

    metadata_args = []
    for k, v in metadata.items():
        metadata_args.append('-metadata')
        metadata_args.append(f'{k}={v}')

    if isinstance(input_file, bytes):
        input_file_name = str(uuid.uuid1())
        input_file_path = pathlib.Path(input_file_name)
        input_file_path.write_bytes(input_file)
    else:
        input_file_name = str(input_file)
        input_file_path = pathlib.Path(input_file)

    if not (extension := input_file_path.suffix.strip('.')):
        extension = await get_format(input_file)
        if 'mp4' in extension:
            extension = 'mp4'

    output_file_name = f'{str(uuid.uuid1())}.{extension}'

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', input_file_name, '-c', 'copy', *metadata_args, output_file_name,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await process.wait()

    if isinstance(input_file, bytes):
        input_file_path.unlink(missing_ok=True)

    output_file_path = pathlib.Path(output_file_name)
    bytes_ = output_file_path.read_bytes()
    output_file_path.unlink(missing_ok=True)

    return bytes_


async def get_format(input_file: bytes | str | pathlib.Path) -> str:
    """Gets media file format."""

    if isinstance(input_file, bytes):
        input_file_name = str(uuid.uuid1())
        input_file_path = pathlib.Path(input_file_name)
        input_file_path.write_bytes(input_file)
    else:
        input_file_name = str(input_file)

    process = await asyncio.create_subprocess_exec(
        'ffprobe', '-show_format', input_file_name,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate()

    if isinstance(input_file, bytes):
        # noinspection PyUnboundLocalVariable
        input_file_path.unlink(missing_ok=True)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return flanautils.find_environment_variables(stdout.decode())['format_name']


async def get_metadata(input_file: bytes | str | pathlib.Path) -> dict:
    """Gets the metadata dictionary of the media file."""

    if isinstance(input_file, bytes):
        input_file_name = str(uuid.uuid1())
        input_file_path = pathlib.Path(input_file_name)
        input_file_path.write_bytes(input_file)
    else:
        input_file_name = str(input_file)

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', input_file_name, '-f', 'ffmetadata', 'pipe:',
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate()

    if isinstance(input_file, bytes):
        # noinspection PyUnboundLocalVariable
        input_file_path.unlink(missing_ok=True)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    metadata = flanautils.find_environment_variables(stdout.decode())

    return {k.lower(): v for k, v in metadata.items()}


# noinspection PyUnboundLocalVariable
async def merge(
    input_file_1: bytes | str | pathlib.Path,
    input_file_2: bytes | str | pathlib.Path = None,
    format_='mp4'
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

    output_file_name = f'{str(uuid.uuid1())}.{format_}'

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

    output_file_path = pathlib.Path(output_file_name)
    bytes_ = output_file_path.read_bytes()
    output_file_path.unlink(missing_ok=True)

    return bytes_


async def to_gif(input_file: bytes | str | pathlib.Path) -> bytes:
    """Convert video to gif."""

    if await get_format(input_file) == 'gif':
        if isinstance(input_file, bytes):
            return input_file
        else:
            return pathlib.Path(input_file).read_bytes()

    if isinstance(input_file, bytes):
        input_file_name = str(uuid.uuid1())
        input_file_path = pathlib.Path(input_file_name)
        input_file_path.write_bytes(input_file)
    else:
        input_file_name = str(input_file)

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', input_file_name, '-vf', 'fps=30,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse', '-loop', '0', '-f', 'gif', 'pipe:',
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate()

    if isinstance(input_file, bytes):
        # noinspection PyUnboundLocalVariable
        input_file_path.unlink(missing_ok=True)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return stdout


async def to_mp3(input_file: bytes | str | pathlib.Path, bitrate=192, sample_rate=44100, channels=2) -> bytes:
    """Extract and return audio in mp3 format from the media file."""

    if await get_format(input_file) == 'mp3':
        if isinstance(input_file, bytes):
            return input_file
        else:
            return pathlib.Path(input_file).read_bytes()

    if isinstance(input_file, bytes):
        input_file_name = str(uuid.uuid1())
        input_file_path = pathlib.Path(input_file_name)
        input_file_path.write_bytes(input_file)
    else:
        input_file_name = str(input_file)

    process = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', input_file_name, '-b:a', f'{bitrate}k', '-ar', str(sample_rate), '-ac', str(channels), '-f', 'mp3', 'pipe:',
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _stderr = await process.communicate()

    if isinstance(input_file, bytes):
        # noinspection PyUnboundLocalVariable
        input_file_path.unlink(missing_ok=True)

    if not stdout:
        raise ValueError('empty ffmpeg stdout')

    return stdout

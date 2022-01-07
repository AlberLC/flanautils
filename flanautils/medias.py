import asyncio
import platform
import subprocess


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

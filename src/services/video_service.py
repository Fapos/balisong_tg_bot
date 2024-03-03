import asyncio
from asyncio.subprocess import create_subprocess_exec


async def generate_video_from_audio(user_id: str, audio_name: str, image_name: str):
    process = await create_subprocess_exec(
        '../ffmpeg/bin/ffmpeg.exe',
        '-i',
        f'../trashbox/{user_id}/audios/{audio_name}',
        '-i',
        f'../trashbox/{user_id}/images/{image_name}',
        '-f',
        'mp4',
        f'../trashbox/{user_id}/videos/{audio_name.rsplit(".", 1)[0] + ".mp4"}'
    )

    _, _ = await process.communicate()




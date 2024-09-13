from discord.ext import commands
import discord
import yt_dlp as youtube_dl
import asyncio
import random

# Настройки YTDL и FFmpeg
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,  # Игнорировать ошибки
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Класс для работы с аудио
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Переменные для хранения состояния
volume_settings = {}
default_volume = None
queue = {}
current_track = {}

def setup(bot):
    @bot.command(name='play', help='Играет музыку по ссылке с YouTube или по названию')
    async def play(ctx, *, query):
        if not ctx.author.voice:
            await ctx.send("Вы должны быть в голосовом канале, чтобы использовать эту команду.")
            return

        voice_channel = ctx.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client:
            voice_client = await voice_channel.connect()
            if default_volume is not None:
                volume_settings[ctx.guild.id] = default_volume

        async with ctx.typing():
            player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
            player.volume = volume_settings.get(ctx.guild.id, default_volume) or 1.0

            if voice_client.is_playing():
                if ctx.guild.id not in queue:
                    queue[ctx.guild.id] = []
                queue[ctx.guild.id].append(player)
                await ctx.send(f'Добавлено в очередь: {player.title}')
            else:
                voice_client.play(player, after=lambda e: bot.loop.create_task(handle_player_end(e, bot, ctx)))
                current_track[ctx.guild.id] = player
                await ctx.send(f'Играет: {player.title}')

    @bot.command(name='setvolume', help='Устанавливает уровень громкости (0.0 - 1.0)')
    async def setvolume(ctx, volume: float):
        if default_volume is not None and not ctx.author.permissions_in(ctx.channel).administrator:
            await ctx.send("Вы не можете изменить уровень громкости, пока установлен стандартный уровень.")
            return

        if not 0.0 <= volume <= 1.0:
            await ctx.send("Уровень громкости должен быть в диапазоне от 0.0 до 1.0.")
            return

        volume_settings[ctx.guild.id] = volume
        if ctx.guild.id in current_track:
            current_track[ctx.guild.id].volume = volume

        await ctx.send(f"Уровень громкости установлен на {volume*100:.0f}%.")

    @bot.command(name='setdefaultvolume', help='Устанавливает стандартный уровень громкости (0.0 - 1.0)')
    @commands.has_permissions(administrator=True)
    async def setdefaultvolume(ctx, volume: float):
        global default_volume
        if not 0.0 <= volume <= 1.0:
            await ctx.send("Уровень громкости должен быть в диапазоне от 0.0 до 1.0.")
            return

        default_volume = volume
        if ctx.guild.id in volume_settings:
            volume_settings[ctx.guild.id] = volume

        if ctx.guild.id in current_track:
            current_track[ctx.guild.id].volume = volume
        
        await ctx.send(f"Стандартный уровень громкости установлен на {volume*100:.0f}%.")

    @bot.command(name='resetdefaultvolume', help='Сбрасывает стандартный уровень громкости')
    @commands.has_permissions(administrator=True)
    async def resetdefaultvolume(ctx):
        global default_volume
        default_volume = None
        if ctx.guild.id in volume_settings:
            del volume_settings[ctx.guild.id]
        await ctx.send("Стандартный уровень громкости сброшен. Пользователи могут снова изменять уровень громкости.")

    @bot.command(name='stop', help='Останавливает музыку и отключает бота')
    async def stop(ctx):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client:
            await ctx.send("Бот не подключен к голосовому каналу.")
            return

        if default_volume is not None and ctx.guild.id in volume_settings:
            volume_settings[ctx.guild.id] = default_volume

        await voice_client.disconnect()

    @bot.command(name='skip', help='Пропускает текущий трек')
    async def skip(ctx):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client or not voice_client.is_playing():
            await ctx.send("В данный момент ничего не воспроизводится.")
            return

        voice_client.stop()
        await ctx.send("Трек пропущен.")
        
        if ctx.guild.id in queue and queue[ctx.guild.id]:
            await play_next_track(ctx, voice_client)
        else:
            if ctx.guild.id in current_track:
                del current_track[ctx.guild.id]

    @bot.command(name='shuffle', help='Перемешивает треки в очереди')
    async def shuffle(ctx):
        if ctx.guild.id not in queue or not queue[ctx.guild.id]:
            await ctx.send("Очередь пуста.")
            return

        random.shuffle(queue[ctx.guild.id])
        await ctx.send("Очередь перемешана.")

    @bot.command(name='queue', help='Показывает список треков в очереди')
    async def queue_command(ctx):
        if ctx.guild.id not in queue or not queue[ctx.guild.id]:
            if ctx.guild.id in current_track:
                await ctx.send(f'Сейчас играет: {current_track[ctx.guild.id].title}')
            else:
                await ctx.send("Очередь пуста.")
            return

        queue_list = [f"{i+1}. {track.title}" for i, track in enumerate(queue[ctx.guild.id])]
        if ctx.guild.id in current_track:
            queue_list.insert(0, f"Сейчас играет: {current_track[ctx.guild.id].title}")
        
        await ctx.send("Очередь треков:\n" + "\n".join(queue_list))

    @bot.command(name='playplaylist', help='Проигрывает плейлист YouTube')
    async def playplaylist(ctx, *, url):
        if not ctx.author.voice:
            await ctx.send("Вы должны быть в голосовом канале, чтобы использовать эту команду.")
            return

        voice_channel = ctx.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client:
            voice_client = await voice_channel.connect()
            if default_volume is not None:
                volume_settings[ctx.guild.id] = default_volume

        async with ctx.typing():
            data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if 'entries' in data:
                entries = data['entries']
                for entry in entries:
                    try:
                        player = await YTDLSource.from_url(entry['url'], loop=bot.loop, stream=True)
                        player.volume = volume_settings.get(ctx.guild.id, default_volume) or 1.0
                        if voice_client.is_playing() or voice_client.is_paused():
                            if ctx.guild.id not in queue:
                                queue[ctx.guild.id] = []
                            queue[ctx.guild.id].append(player)
                            await ctx.send(f'Добавлено в очередь: {player.title}')
                        else:
                            voice_client.play(player, after=lambda e: bot.loop.create_task(handle_player_end(e, bot, ctx)))
                            current_track[ctx.guild.id] = player
                            await ctx.send(f'Играет: {player.title}')
                    except Exception as e:
                        await ctx.send(f"Пропущено: {entry['title']} (Ошибка: {str(e)})")

    async def handle_player_end(error, bot, ctx):
        if error:
            await ctx.send(f"Произошла ошибка: {str(error)}")

        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        await play_next_track(ctx, voice_client)

    async def play_next_track(ctx, voice_client):
        if ctx.guild.id in queue and queue[ctx.guild.id]:
            next_track = queue[ctx.guild.id].pop(0)
            voice_client.play(next_track, after=lambda e: bot.loop.create_task(handle_player_end(e, bot, ctx)))
            current_track[ctx.guild.id] = next_track
            await ctx.send(f'Играет следующий трек: {next_track.title}')
        else:
            if ctx.guild.id in current_track:
                del current_track[ctx.guild.id]

# Не забудьте подключить этот файл к основному файлу bot.py

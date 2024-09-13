import sqlite3
from discord.ext import commands
import discord

# Путь к базе данных SQLite
DATABASE_PATH = 'responses.db'

message_status = False

def init_db():
    """Создает таблицу в базе данных, если она не существует"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                word TEXT PRIMARY KEY,
                phrase TEXT NOT NULL,
                user_id INTEGER NOT NULL
            )
        ''')
        conn.commit()


async def setup(bot):
    print("Setting up botthree...")
    init_db()

    def is_admin(ctx):
        return ctx.author.guild_permissions.administrator

    @commands.check(is_admin)
    @bot.command(name='command', aliases=['команда'])
    async def add_command(ctx, слово: str, *, фраза: str):
        """Command for adding "word" and "phrase" pairs"""
        print(f"Command !command/!команда called with parameters: word='{слово}', phrase='{фраза}'")  # Debug line
        слово = слово.strip('"').lower()  # Remove quotes and convert to lowercase
        фраза = фраза.strip('"')  # Remove quotes
        user_id = ctx.author.id
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO responses (word, phrase, user_id) VALUES (?, ?, ?)
            ''', (слово, фраза, user_id))
            conn.commit()
        await ctx.send(f'Pair added: "{слово}" -> "{фраза}" / Пара добавлена: "{слово}" -> "{фраза}"')

    @commands.check(is_admin)
    @bot.command(name='deletecommand', aliases=['удалитькоманда'])
    async def delete_command(ctx, слово: str):
        """Command for deleting a record by word"""
        print(f"Command !deletecommand/!удалитькоманда called with parameter: word='{слово}'")  # Debug line
        слово = слово.strip('"').lower()  # Remove quotes and convert to lowercase

        # Check if the record with the given word exists
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM responses WHERE word = ?', (слово,))
            if cursor.fetchone() is not None:
                # Record exists, delete it
                cursor.execute('DELETE FROM responses WHERE word = ?', (слово,))
                conn.commit()
                await ctx.send(f'Record with key "{слово}" deleted from the database. / Запись с ключом "{слово}" удалена из базы данных.')
            else:
                # Record not found
                await ctx.send(f'Record with key "{слово}" not found. / Запись с ключом "{слово}" не найдена.')

        # Show updated list of records
        await ctx.invoke(bot.get_command('words'))

    @commands.check(is_admin)
    @bot.command(name='clearwords', aliases=['очиститьслова'])
    async def clear_words(ctx):
        """Command for deleting all records from the database"""
        print("Command !clearwords/!очиститьслова called")  # Debug line
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM responses')
            conn.commit()
        await ctx.send('All records deleted from the database. / Все записи удалены из базы данных.')

        # Show updated list of records
        await ctx.invoke(bot.get_command('words'))

    @commands.check(is_admin)
    @bot.command(name='clearuserwords', aliases=['очиститьсловаюзер'])
    async def clear_user_words(ctx):
        """Command for deleting user's records"""
        print("Command !clearuserwords/!очиститьсловаюзер called")  # Debug line
        user_id = ctx.author.id
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM responses WHERE user_id = ?', (user_id,))
            conn.commit()
        await ctx.send('All records of the user deleted from the database. / Все записи пользователя удалены из базы данных.')

        # Show updated list of records
        await ctx.invoke(bot.get_command('words'))

    @bot.command(name='words', aliases=['слова'])
    async def list_records(ctx):
        """Command for displaying all records from the database"""
        print("Command !words/!слова called")  # Debug line
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word, phrase FROM responses')
            rows = cursor.fetchall()
            
            if rows:
                response = '\n'.join([f'Key: "{row[0]}", Phrase: "{row[1]}"' for row in rows])
                await ctx.send(f'Record list:\n{response} / Список записей:\n{response}')
            else:
                await ctx.send('The database is empty. / База данных пуста.')

    @commands.check(is_admin)
    @bot.command(name='wordsstatus', aliases=['словастатус'])
    async def toggle_status(ctx):
        """Command to toggle the status of message handling"""
        global message_status
        message_status = not message_status
        status_message = "Status enabled / Статус включен" if message_status else "Status disabled / Статус выключен"
        await ctx.send(status_message)

    @bot.event
    async def on_message(message):
        """Message handler"""
        # Ignore messages from the bot itself
        if message.author == bot.user:
            return
        
        content = message.content.lower()

        # Only process messages if status is enabled
        if not message_status:
            await bot.process_commands(message)
            return




        #----------------------РУССКИЙ------------------------------

        # Check message content and respond
        if any(word in content.split() for word in ["аниме"]):
            image_url = "https://i.postimg.cc/hGVw1H8J/images-3.jpg"
            await message.channel.send(image_url)

        if any(word in content.split() for word in ["ахуеть"]):
            await message.channel.send("пиздишь")

        if any(word in content.split() for word in ["пиздатый"]):
            await message.channel.send("пиздишь")

        if any(word in content.split() for word in ["рт"]):
            await message.channel.send("иди нахуй")

        if any(word in content.split() for word in ["подумал", "думал", "думаю", "знаю"]):
            await message.channel.send("не думай")

        if any(word in content.split() for word in ["пидор"]):
            await message.channel.send("сам пидор")

        if any(word in content.split() for word in ["канал", "каналы"]):
            await message.channel.send("аналы")

        if any(word in content.split() for word in ["ахуенная", "ахуенный", "ахуенное", "лучше"]):
            await message.channel.send("хуйня")

        if any(word in content.split() for word in ["телефон"]):
            await message.channel.send("сосни за айфон")

        if any(word in content.split() for word in ["фулл", "фулловый", "фуловый", "фул"]):
            await message.channel.send("ПРОШУ ФУЛЛ")

        if any(word in content.split() for word in ["идите нахуй", "иди нахуй", "пошел нахуй", "хуй", "пидорасы"]):
            await message.channel.send("присел ты нахуй")

        if any(word in content.split() for word in ["аффикс", "афикс", "аффиксы", "афиксы", "аффиксов", "афиксов"]):
            await message.channel.send("ебанутые аффиксы, нахуй я на этом сервере играю")

        if any(word in content.split() for word in ["ушош", "ушоша", "ушошем", "ушоше", "ювов", "uwow"]):
            await message.channel.send("опять упал?")

        if any(word in content.split() for word in ["да"]):
            await message.channel.send("пизда")
        
        if content == "нет":
            await message.channel.send("https://i.postimg.cc/QNkRK9hp/c3c80ca980689364b7ffafad01246a1d.jpg")

        #-------------------------------------------------------------------

        #--------------------ИНГЛИШ-----------------------------------------

        if any(word in content.split() for word in ["anime"]):
            image_url = "https://i.postimg.cc/mkJpMH2s/images-3.jpg"
            await message.channel.send(image_url)

        if any(word in content.split() for word in ["wow"]):
            await message.channel.send("you're fucking")

        if any(word in content.split() for word in ["pussy"]):
            await message.channel.send("you're fucking")

        if any(word in content.split() for word in ["RT"]):
            await message.channel.send("go fuck yourself")

        if any(word in content.split() for word in ["thought", "thought", "think", "know"]):
            await message.channel.send("don't think")

        if any(word in content.split() for word in ["fag"]):
            await message.channel.send("he's a fag himself")

        if any(word in content.split() for word in ["channel", "channels"]):
            await message.channel.send("anals")

        if any(word in content.split() for word in ["awesome", "awesome", "awesome", "better"]):
            await message.channel.send("bullshit")

        if any(word in content.split() for word in ["telephone"]):
            await message.channel.send("pine for the iPhone")

        if any(word in content.split() for word in ["full", "ful"]):
            await message.channel.send("I ASK FOR FULL")

        if any(word in content.split() for word in ["fuck you", "fuck you", "fuck you", "fuck", "faggots"]):
            await message.channel.send("fuck you sat down")

        if any(word in content.split() for word in ["affix", "afix", "affixes", "afixes", "affixes", "afixes"]):
            await message.channel.send("fucking affixes, fuck me I play on this server")

        if any(word in content.split() for word in ["uwow"]):
            await message.channel.send("The server crashed again?")

        if any(word in content.split() for word in ["Yes"]):
            await message.channel.send("pussy")
        
        if content == "no":
            await message.channel.send("https://i.postimg.cc/hvtRMTBQ/fff.jpg")

        #-----------------------------------------------------------------------------------------------------







        # Search for user-defined "word" -> "phrase" pairs in the database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT phrase FROM responses WHERE word = ?', (content,))  # Word in the message
            result = cursor.fetchone()
            if result:
                await message.channel.send(result[0])

        # Don't forget to process commands
        await bot.process_commands(message)

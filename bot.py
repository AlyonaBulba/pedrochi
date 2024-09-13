import sqlite3
import discord
from discord.ext import commands
from datetime import datetime, date
import os
from discord.ui import Button, View
import botwo
import botthree  # Импортируем файл botthree.py

# Глобальная переменная
allow_same_day = False
waiting_for_input = {}

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Инициализация базы данных
def get_db_connection():
    conn = sqlite3.connect('reminders.db')
    return conn

def initialize_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            info TEXT,
            user_id INTEGER
        );
    ''')
    conn.commit()
    conn.close()

initialize_db()

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен и готов к работе!')
    await botthree.setup(bot)  # Ожидаем setup
    botwo.setup(bot)

@bot.command(name='restart', aliases=['рестарт'])
@commands.has_permissions(administrator=True)
async def restart(ctx):
    await ctx.send("Restart...")
    await bot.close()
    os.system('py bot.py')

@bot.command(name='request', aliases=['запрос'])
async def request(ctx):
    await ctx.send("Напиши свой возраст, You age:")
    waiting_for_input[ctx.author.id] = 'age_input'

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.id in waiting_for_input:
        action = waiting_for_input.pop(message.author.id)
        conn = get_db_connection()
        c = conn.cursor()
        try:
            if action == 'delete_id':
                message_id = int(message.content)
                c.execute("DELETE FROM reminders WHERE id = ?", (message_id,))
                if c.rowcount > 0:
                    conn.commit()
                    await message.channel.send(f"Запись с id {message_id} удалена. Recording with id {message_id} deleted.")
                    await show_list(message.channel)  # Показать обновленный список
                else:
                    await message.channel.send(f"Запись с id {message_id} не найдена. Recording with id {message_id} not found.")
            elif action == 'age_input':
                age = int(message.content)
                await message.channel.send(f"Ты большой! Твой возраст: {age}. You big! Your age: {age}.")
            elif action == 'delete_user':
                user_id = int(message.content)
                c.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
                conn.commit()
                rows_deleted = c.rowcount
                if rows_deleted > 0:
                    await message.channel.send(f"Все записи пользователя с ID {user_id} были удалены. Удалено {rows_deleted} записей. All records for user ID {user_id} deleted. Deleted {rows_deleted} records.")
                    await show_list(message.channel)
                else:
                    await message.channel.send(f"Записей пользователя с ID {user_id} не найдено. No records found for user ID {user_id}.")
            elif action == 'delete_date':
                date_str = message.content
                date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
                c.execute("DELETE FROM reminders WHERE date = ?", (date_obj,))
                conn.commit()
                rows_deleted = c.rowcount
                if rows_deleted > 0:
                    await message.channel.send(f"Все записи на {date_obj.strftime('%d.%m.%Y')} удалены. All records for {date_obj.strftime('%d.%m.%Y')} deleted.")
                    await show_list(message.channel)
                else:
                    await message.channel.send(f"Записей на {date_obj.strftime('%d.%m.%Y')} не найдено. No records found for {date_obj.strftime('%d.%m.%Y')}.")
        except ValueError:
            await message.channel.send("Пожалуйста, введите корректное значение. Please enter the correct value.")
        finally:
            conn.close()
    
    await bot.process_commands(message)

@bot.command()
async def pepe(ctx):
    emoji = "<:customemoji:1283695138530656329>"  # Замените на реальное имя и ID эмодзи
    await ctx.send(f'{emoji}')
    await ctx.message.delete()

@bot.command()
async def image(ctx):
    image_url = "https://i.postimg.cc/g02CYcgR/images-2.jpg"
    await ctx.send(image_url)

@bot.command(name='record', aliases=['запись'])
async def record(ctx, date_str: str, *, info: str):
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        today = date.today()
        user_id = ctx.author.id
        has_role = any(role.name == 'Гос Дума' for role in ctx.author.roles)

        if date_obj < today:
            await ctx.send("Вы не можете добавить запись на прошедшую дату. You cannot add an entry for a past date.")
            return

        if not has_role and not allow_same_day and date_obj == today:
            await ctx.send("Запись на сегодняшний день запрещена. Recording for today is not allowed.")
            return

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM reminders WHERE date = ? AND user_id = ?", (date_obj, user_id))
        count = c.fetchone()[0]

        if count > 0 and not has_role:
            await ctx.send("Вы уже добавляли запись на эту дату. Только одна запись на день разрешена. You have already added an entry for this date. Only one entry per day is allowed.")
        else:
            c.execute("INSERT INTO reminders (date, info, user_id) VALUES (?, ?, ?)", (date_obj, info, user_id))
            conn.commit()
            last_id = c.lastrowid
            await ctx.send(f"Запись добавлена на {date_obj.strftime('%d.%m.%Y')} с id {last_id}. Recording added on {date_obj.strftime('%d.%m.%Y')} with id {last_id}.")
        conn.close()
    except ValueError:
        await ctx.send("Неправильный формат даты. Используйте формат ДД.ММ.ГГГГ. The date format is incorrect. Use the format DD.MM.YYYY.")
    except sqlite3.Error as e:
        await ctx.send(f"Ошибка базы данных: {e}. Database error: {e}.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка: {e}. Error: {e}.")

@bot.command(name='day', aliases=['день'])
@commands.has_permissions(administrator=True)
async def day(ctx):
    global allow_same_day
    allow_same_day = not allow_same_day
    status = "разрешено" if allow_same_day else "запрещено"
    await ctx.send(f"Запись на сегодняшний день теперь {status}. Recording for today is now {status}.")

@bot.command(name='clearid', aliases=['очиститьайди'])
@commands.has_permissions(administrator=True)
async def clearid(ctx, id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id = ?", (id,))
    if c.rowcount > 0:
        conn.commit()
        await ctx.send(f"Запись с id {id} удалена. Recording with id {id} deleted.")
    else:
        await ctx.send(f"Запись с id {id} не найдена. Recording with id {id} not found.")
    await show_list(ctx.channel)
    conn.close()

@bot.command(name='clearallid', aliases=['очиститьвсеайди'])
@commands.has_permissions(administrator=True)
async def clearallid(ctx):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reminders")
        conn.commit()
        c.execute("DELETE FROM sqlite_sequence WHERE name='reminders'")
        conn.commit()
        conn.close()
        await ctx.send("Все записи удалены и автоинкрементный счетчик сброшен. All records deleted and the auto-increment counter has been reset.")
    except sqlite3.Error as e:
        await ctx.send(f"Произошла ошибка: {e}. Error: {e}.")
    await show_list(ctx)

@bot.command(name='clearlist', aliases=['очиститьсписок'])
@commands.has_permissions(administrator=True)
async def clearlist(ctx):
    # Создание кнопки для очистки всех ID
    button = Button(label="Clear all IDs_Очистить все ID", style=discord.ButtonStyle.danger)

    async def button1_callback(interaction):
        await ctx.invoke(bot.get_command('clearallid'))
        await interaction.response.send_message("Все ID очищены. All IDs have been cleared.")
        await show_list(interaction.channel)  # Показать обновленный список

    button.callback = button1_callback

    # Создание View и добавление кнопки
    view = View()
    view.add_item(button)

    # Отправляем сообщение с кнопкой
    await ctx.send("Вы хотите очистить все ID после удаления всех записей? Do you want to clear all IDs after deleting all records?", view=view)

    try:
        # Очистка записей
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reminders")
        conn.commit()
        conn.close()
        await ctx.send("Все записи удалены. All records deleted.")
    except sqlite3.Error as e:
        await ctx.send(f"Произошла ошибка: {e}. Error: {e}.")

    # Обновленный список будет показан после нажатия кнопки

@bot.command(name='clearuser', aliases=['очиститьюзер'])
@commands.has_permissions(administrator=True)
async def clearuser(ctx, user_id: int):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        conn.commit()
        rows_deleted = c.rowcount
        if rows_deleted > 0:
            await ctx.send(f"Все записи пользователя с ID {user_id} были удалены. Удалено {rows_deleted} записей. All records for user ID {user_id} deleted. Deleted {rows_deleted} records.")
        else:
            await ctx.send(f"Записей пользователя с ID {user_id} не найдено. No records found for user ID {user_id}.")
        conn.close()
    except sqlite3.Error as e:
        await ctx.send(f"Произошла ошибка: {e}. Error: {e}.")

@bot.command(name='cleardate', aliases=['очиститьдату'])
@commands.has_permissions(administrator=True)
async def cleardate(ctx, date_str: str):
    try:
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE date = ?", (date_obj,))
        conn.commit()
        rows_deleted = c.rowcount
        if rows_deleted > 0:
            await ctx.send(f"Все записи на {date_obj.strftime('%d.%m.%Y')} удалены. All records for {date_obj.strftime('%d.%m.%Y')} deleted.")
        else:
            await ctx.send(f"Записей на {date_obj.strftime('%d.%m.%Y')} не найдено. No records found for {date_obj.strftime('%d.%m.%Y')}.")
        conn.close()
    except ValueError:
        await ctx.send("Неправильный формат даты. Используйте формат ДД.ММ.ГГГГ. The date format is incorrect. Use the format DD.MM.YYYY.")
    except sqlite3.Error as e:
        await ctx.send(f"Произошла ошибка: {e}. Error: {e}.")

@bot.command(name='list', aliases=['список'])
async def show_list(ctx):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, date, info FROM reminders ORDER BY date")
    rows = c.fetchall()
    if rows:
        message = "Список записей:\n"
        for row in rows:
            message += f"ID: {row[0]}, Дата: {row[1]}, Информация: {row[2]}\n"
        await ctx.send(message)
    else:
        await ctx.send("Список пуст. The list is empty.")
    conn.close()



# Запуск бота
bot.run('MTI3OTQ4MjI0ODM1NzIyMDUxOQ.GYeal9.sI_5Bft78SIn3b7zV8oq-aKHh4nojYrV7e4NfQ')  # Замените на реальный токен
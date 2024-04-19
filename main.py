from aiogram import Bot, Dispatcher
from aiogram.filters import Text, Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key("key")
yn = ['✅', '❌']


async def get_users():
    users = [int(i) for i in sheet.get_worksheet(1).col_values(2)[1:] + sheet.get_worksheet(1).col_values(1)[1:]]
    return users


async def get_workers():
    users = [int(i) for i in sheet.get_worksheet(1).col_values(2)[1:]]
    return users


async def get_admins():
    users = [int(i) for i in sheet.get_worksheet(1).col_values(1)[1:]]
    return users


async def get_text():
    users = sheet.get_worksheet(0).col_values(1)[1:]
    return users


def set_buttons(text):
    temp = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='❌ ' + i,
                callback_data='❌ ' + i)] for i in text])
    temp.inline_keyboard.append([InlineKeyboardButton(text='📤 Отправить на проверку', callback_data='check')])
    return temp


def edit_buttons(reply_markup, data):
    reply_markup = reply_markup.inline_keyboard
    temp = reply_markup.index([InlineKeyboardButton(text=data, callback_data=data)])
    reply_markup[temp] = [InlineKeyboardButton(text=yn[abs(yn.index(data[0]) - 1)] + data[1:],
                                               callback_data=yn[abs(yn.index(data[0]) - 1)] + data[1:])]
    return InlineKeyboardMarkup(inline_keyboard=reply_markup)


BOT_TOKEN = 'BOT_TOKEN'

bot: Bot = Bot(token=BOT_TOKEN)
dp: Dispatcher = Dispatcher()


@dp.message(Command(commands=['start']))
async def start_command(message: Message):
    print(message.from_user.id)
    if not message.from_user.id in await get_users():
        await message.answer('Вас нет в базе пользователей')
        return
    print('ok')
    await message.answer('Добро пожаловать')


@dp.message(Command(commands=['send']))
async def send_command(message: Message):
    if not message.from_user.id in await get_admins():
        return
    text = await get_text()
    msg = await message.answer('Начало рассылки заданий')
    for i in await get_workers():
        try:
            await bot.send_message(chat_id=i, text='Работа', reply_markup=set_buttons(text))
            await asyncio.sleep(2.5)

        except:
            pass
    await msg.edit_text('Рассылка завершена')


@dp.callback_query(Text(text=['check']))
async def check(callback: CallbackQuery):
    temp = "\n".join([i[0].text for i in callback.message.reply_markup.inline_keyboard[:-1]])
    await callback.message.edit_text(text=f'Отправлено\n\n'
                                          f'{temp}')
    for i in await get_admins():
        try:
            await bot.send_message(chat_id=i, text=f'@{callback.from_user.username} {callback.from_user.first_name}\n'
                                                   f'Отправил на проверку чек-лист\n\n'
                                                   f'{temp}',
                                   reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm')]]))
            await asyncio.sleep(2.5)
        except:
            pass


@dp.callback_query(Text(text=['confirm']))
async def confirm(callback: CallbackQuery):
    await callback.message.edit_text(text=callback.message.text + '\n\n Вы подтвердили выполнение задач')


@dp.callback_query()
async def checkpoint(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=edit_buttons(callback.message.reply_markup, callback.data))


if __name__ == '__main__':
    dp.run_polling(bot)

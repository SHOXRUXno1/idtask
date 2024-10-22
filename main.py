import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import uuid  # Для генерации уникальных идентификаторов задач

# Bot token
TOKEN = "7695838711:AAEne9ai-xk2m_6S-2lNoEcXg7ai1S6z5Ds"  # Замените на ваш токен
ADMIN_ID = 114253636

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Список сотрудников
employees = {}
tasks = {}  # Хранение заданий для каждого сотрудника

# Статусы
class AddEmployee(StatesGroup):
    waiting_for_employee_id = State()
    waiting_for_employee_position = State()

class AssignTask(StatesGroup):
    waiting_for_task = State()
    chosen_employee_id = State()

class RemoveEmployee(StatesGroup):
    waiting_for_employee_to_remove = State()

# Админская клавиатура
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 - Xodim qo'shish 🤝")],
        [KeyboardButton(text="2 - Xodimga xabar yozish 📨")],
        [KeyboardButton(text="3 - Xodimni o'chirish ❌")]
    ],
    resize_keyboard=True
)

# Клавиатура для обычных пользователей
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="2 - Xodimga xabar yozish 📨")],
    ],
    resize_keyboard=True
)

# Клавиатура с кнопкой "Назад"
back_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Orqaga ↩️")]
    ],
    resize_keyboard=True
)

# Начальный командный обработчик
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:  # ID администратора
        await message.answer("Ishni tanlang: 🤔", reply_markup=admin_keyboard)
    else:
        await message.answer(f"Salom, {message.from_user.full_name}!👋\nSizning ID: `{message.from_user.id}`",
                             parse_mode="Markdown", reply_markup=user_keyboard)

# Процесс добавления сотрудника
@dp.message(lambda message: message.text == "1 - Xodim qo'shish 🤝")
async def add_employee_start(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, xodimning Telegram ID'sini kiriting: 🆔")
    await state.set_state(AddEmployee.waiting_for_employee_id)

@dp.message(AddEmployee.waiting_for_employee_id)
async def employee_id_received(message: types.Message, state: FSMContext):
    await state.update_data(employee_id=message.text)
    await message.answer("Iltimos, xodimning lavozimini kiriting: 🏢")
    await state.set_state(AddEmployee.waiting_for_employee_position)

@dp.message(AddEmployee.waiting_for_employee_position)
async def employee_position_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['employee_id']
    employee_position = message.text
    employees[employee_id] = employee_position
    await message.answer(f"Xodim ID {employee_id} va lavozimi '{employee_position}' qo'shildi. 🎉")
    await message.answer("Orqaga qaytish uchun tugmani bosing:", reply_markup=back_keyboard)
    await state.clear()

# Обработка кнопки "Orqaga"
@dp.message(lambda message: message.text == "Orqaga ↩️")
async def go_back(message: types.Message):
    if message.from_user.id == ADMIN_ID:  # ID администратора
        await message.answer("Ishni tanlang: 🤔", reply_markup=admin_keyboard)
    else:
        await message.answer("Ishni tanlang: 🤔", reply_markup=user_keyboard)

# Процесс удаления сотрудника
@dp.message(lambda message: message.text == "3 - Xodimni o'chirish ❌")
async def remove_employee_start(message: types.Message):
    if not employees:
        await message.answer("Xodimlar hali mavjud emas. 😔")
        return

    # Создание клавиатуры с кнопками для удаления сотрудников
    inline_keyboard = [
        [InlineKeyboardButton(text=f"{employee_id} - {position}", callback_data=f"remove_{employee_id}")]
        for employee_id, position in employees.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer("O'chirish uchun xodimni tanlang: ❌", reply_markup=keyboard)

# Обработка выбора сотрудника для удаления
@dp.callback_query(lambda c: c.data and c.data.startswith("remove_"))
async def employee_to_remove(callback_query: types.CallbackQuery):
    employee_id = callback_query.data.split("_")[1]

    if employee_id in employees:
        employee_position = employees[employee_id]
        del employees[employee_id]  # Удаляем сотрудника из списка

        await bot.send_message(callback_query.from_user.id,
                               f"Xodim ID {employee_id} va lavozimi '{employee_position}' o'chirildi. ✅")
        await bot.send_message(callback_query.from_user.id, "Orqaga qaytish uchun tugmani bosing:",
                               reply_markup=back_keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, "Xodim topilmadi. 😞")

    await bot.answer_callback_query(callback_query.id)

# Процесс отправки сообщения сотруднику
@dp.message(lambda message: message.text == "2 - Xodimga xabar yozish 📨")
async def choose_employee_for_task(message: types.Message):
    if not employees:
        await message.answer("Xodimlar hali mavjud emas. 😔")
        return

    # Создание клавиатуры для выбора сотрудника
    inline_keyboard = [
        [InlineKeyboardButton(text=f"{position}", callback_data=f"choose_{employee_id}")]
        for employee_id, position in employees.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer("Xodimni tanlang: 🧑‍💼", reply_markup=keyboard)

# Обработка выбора сотрудника для задания
@dp.callback_query(lambda c: c.data and c.data.startswith("choose_"))
async def employee_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    employee_id = callback_query.data.split("_")[1]
    employee_position = employees.get(employee_id)  # Получаем должность по ID сотрудника

    if employee_position is None:
        await bot.send_message(callback_query.from_user.id, "Xodim topilmadi. 😞")
        await bot.answer_callback_query(callback_query.id)
        return

    await state.update_data(chosen_employee_id=employee_id)
    await bot.send_message(
        callback_query.from_user.id,
        f"Siz ( {employee_position} ) - 👨‍💼 bo'lgan xodimni tanladingiz. Vazifani yozing: 📝"
    )
    await state.set_state(AssignTask.waiting_for_task)
    await bot.answer_callback_query(callback_query.id)

@dp.message(AssignTask.waiting_for_task)
async def task_assigned(message: types.Message, state: FSMContext):
    data = await state.get_data()
    employee_id = data['chosen_employee_id']
    task_text = message.text

    if employee_id not in employees:
        await message.answer("Xodim topilmadi, iltimos yana urinib ko'ring. 🙁")
        return

    # Генерируем уникальный идентификатор для задачи
    task_id = str(uuid.uuid4())

    # Сохраняем задачу для сотрудника с уникальным идентификатором
    tasks[task_id] = {"employee_id": employee_id, "task": task_text, "sender_id": message.from_user.id}

    # Логируем, что задача добавлена
    logging.info(f"Task added: {task_id} for employee {employee_id}")

    # Создаем inline-кнопки "Сделал" и "Не сделал"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сделал ✅", callback_data=f"done_{task_id}"),
            InlineKeyboardButton(text="Не сделал ❌", callback_data=f"not_done_{task_id}")
        ]
    ])

    # Отправляем задачу сотруднику с указанием отправителя
    sender_name = message.from_user.full_name  # Получаем имя отправителя
    await bot.send_message(
        employee_id,
        f'Sizga vazifa yuklandi: {task_text} 📋\n\nYuborgan: {sender_name} (ID: {message.from_user.id})',
        reply_markup=keyboard
    )

    # Отправляем сообщение админу с подтверждением и кнопкой "Назад"
    await message.answer(f"Vazifa ({employees[employee_id]}) 👨‍💼 bo'lgan xodimga yuborildi. 📬",
                         reply_markup=back_keyboard)

    await state.clear()

# Обработка выполнения задачи
@dp.callback_query(lambda c: c.data and (c.data.startswith("done_") or c.data.startswith("not_done_")))
async def task_done_or_not(callback_query: types.CallbackQuery):
    logging.info(f"Received callback data: {callback_query.data}")

    # Разбиваем данные на части
    action, task_id = callback_query.data.rsplit("_", 1)

    task_info = tasks.get(task_id)

    if task_info:
        employee_id = task_info['employee_id']
        task_text = task_info['task']
        sender_id = task_info['sender_id']

        # Получаем имя отправителя (админ или другой пользователь)
        sender = await bot.get_chat(sender_id)
        sender_name = sender.full_name if sender else "Неизвестный отправитель"

        if action == "done":
            await bot.send_message(sender_id,
                                   f"Xodim {employees[employee_id]} - 👨‍💼 vazifani bajardi:\nVazifa:  {task_text} ✅")
            await bot.send_message(employee_id, "Raxmat - 👍, Siz bajardingiz - ✅")
        else:
            await bot.send_message(sender_id,
                                   f"Xodim {employees[employee_id]} - 👨‍💼 vazifani bajarmadi: \nVazifa: {task_text} ❌")
            await bot.send_message(employee_id, "Raxmat - 👍, Siz bajarmadingiz - ❌")  # Сообщение для сотрудника

        # Удаляем задачу из словаря
        del tasks[task_id]

    await bot.answer_callback_query(callback_query.id)

async def set_commands():
    commands = [
        types.BotCommand(command="start", description="Botni ishga tushirish"),
    ]
    await bot.set_my_commands(commands)

# Запуск бота
async def on_startup(dp):
    await set_commands()  # Установка команд при запуске

async def main():
    await on_startup(dp)  # Вызов ваших функций инициализации
    await dp.start_polling(bot)  # Передаем экземпляр бота

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

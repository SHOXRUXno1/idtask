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
TOKEN = "7261556871:AAH7kkSsAxa9Iibu3Vy_dfjo20KPMlKoTjM"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Xodimlarni saqlash uchun ro'yxat
employees = {}
tasks = {}  # Хранение заданий для каждого сотрудника


# Holatlar
class AddEmployee(StatesGroup):
    waiting_for_employee_id = State()
    waiting_for_employee_position = State()


class AssignTask(StatesGroup):
    waiting_for_task = State()
    chosen_employee_id = State()


class RemoveEmployee(StatesGroup):
    waiting_for_employee_to_remove = State()


# Admin uchun klaviatura
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 - Xodim qo'shish 🤝")],
        [KeyboardButton(text="2 - Xodimga xabar yozish 📨")],
        [KeyboardButton(text="3 - Xodimni o'chirish ❌")]
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


# Boshlang'ich buyruq
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == 6699675868:  # Asl admin ID-si
        await message.answer("Ishni tanlang: 🤔", reply_markup=admin_keyboard)
    else:
        await message.answer(f"Salom, {message.from_user.full_name}!👋\nSizning ID: `{message.from_user.id}`", parse_mode="Markdown")


# Xodim qo'shish jarayoni
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
    await message.answer("Ishni tanlang: 🤔", reply_markup=admin_keyboard)


# Xodimni o'chirish jarayoni
@dp.message(lambda message: message.text == "3 - Xodimni o'chirish ❌")
async def remove_employee_start(message: types.Message):
    if not employees:
        await message.answer("Xodimlar hali mavjud emas. 😔")
        return

    # Tugmalar bilan klaviatura yaratish
    inline_keyboard = [
        [InlineKeyboardButton(text=f"{employee_id} - {position}", callback_data=f"remove_{employee_id}")]
        for employee_id, position in employees.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer("O'chirish uchun xodimni tanlang: ❌", reply_markup=keyboard)


# Xodimni o'chirish uchun tanlovni qayta ishlash
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


# Xodimga vazifa yuborish jarayoni
@dp.message(lambda message: message.text == "2 - Xodimga xabar yozish 📨")
async def choose_employee_for_task(message: types.Message):
    if not employees:
        await message.answer("Xodimlar hali mavjud emas. 😔")
        return

    # Tugmalar bilan klaviatura yaratish
    inline_keyboard = [
        [InlineKeyboardButton(text=f"{position}", callback_data=f"choose_{employee_id}")]
        for employee_id, position in employees.items()
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer("Xodimni tanlang: 🧑‍💼", reply_markup=keyboard)


# Vazifa uchun xodimni tanlashni qayta ishlash
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
    tasks[task_id] = {"employee_id": employee_id, "task": task_text}

    # Создаем inline-кнопки "Сделал" и "Не сделал"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сделал ✅", callback_data=f"done_{task_id}"),
            InlineKeyboardButton(text="Не сделал ❌", callback_data=f"not_done_{task_id}")
        ]
    ])

    # Отправляем задачу сотруднику с inline-кнопками
    await bot.send_message(employee_id, f"Sizga vazifa yuklandi: {task_text} 📋", reply_markup=keyboard)

    # Отправляем сообщение админу с подтверждением и кнопкой "Назад"
    await message.answer(f"Vazifa ({employees[employee_id]}) bo'lgan xodim ga yuborildi. 📬", reply_markup=back_keyboard)

    await state.clear()


# Обработка выполнения задачи
@dp.callback_query(lambda c: c.data and (c.data.startswith("done_") or c.data.startswith("not_done_")))
async def task_done_or_not(callback_query: types.CallbackQuery):
    task_id = callback_query.data.split("_")[1]
    task_data = tasks.get(task_id)

    if not task_data:
        await bot.send_message(callback_query.from_user.id, "Vazifa topilmadi. 😞")
        await bot.answer_callback_query(callback_query.id)
        return

    employee_id = task_data["employee_id"]
    task_text = task_data["task"]

    if callback_query.data.startswith("done_"):
        await bot.send_message(6699675868, f"{employees[employee_id]} xodimi vazifani bajardi: {task_text} ✅")
        await bot.send_message(employee_id, "Rahmat, vazifani bajardingiz! ✅")
    else:
        await bot.send_message(6699675868, f"{employees[employee_id]} xodimi vazifani bajarmadi: {task_text} ❌")
        await bot.send_message(employee_id, "Vazifa bajarmadingiz. ❌")

    await bot.answer_callback_query(callback_query.id)
    del tasks[task_id]  # Удаляем задачу после ответа


# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))

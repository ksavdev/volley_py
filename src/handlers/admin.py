# src/handlers/admin.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src.config import ADMINS
from src.states.admin_states import AdminDMStates, AdminStates
from src.keyboards.back_cancel import back_cancel_kb

router = Router()

@router.message(Command("dm"))
async def start_dm(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ У вас нет прав.")
    await message.reply("Введите chat_id пользователя:")
    await state.set_state(AdminDMStates.waiting_for_user_id)

@router.message(AdminDMStates.waiting_for_user_id)
async def got_target(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except ValueError:
        return await message.reply("❌ Нужно ввести число. Повторите:")
    await state.update_data(user_id=uid)
    await message.reply("Теперь введите текст сообщения:")
    await state.set_state(AdminDMStates.waiting_for_text)

@router.message(AdminDMStates.waiting_for_text)
async def got_text(message: Message, state: FSMContext):
    data = await state.get_data()
    uid  = data["user_id"]
    text = message.text
    try:
        await message.bot.send_message(chat_id=uid, text=text)
        await message.reply("✅ Сообщение отправлено.")
    except Exception as e:
        await message.reply(f"Ошибка при отправке: {e!r}")
    finally:
        await state.clear()

@router.message(AdminStates.waiting_for_broadcast_text)
async def admin_broadcast_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Рассылка отменена.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Выберите действие администратора.", reply_markup=None)
        await state.set_state(AdminStates.waiting_for_action)
        return

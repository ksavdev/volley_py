from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from src.states.hall_request_states import HallRequestStates
from src.config import ADMINS

router = Router(name="hall_request")

@router.message(HallRequestStates.waiting_for_hall_name)
async def got_hall_name(msg: Message, state: FSMContext):
    await state.update_data(hall_name=msg.text.strip())
    await msg.answer("📍 Теперь введите адрес зала (город, улица, дом):")
    await state.set_state(HallRequestStates.waiting_for_hall_address)

@router.message(HallRequestStates.waiting_for_hall_address)
async def got_hall_address(msg: Message, state: FSMContext):
    data = await state.get_data()
    hall_name = data["hall_name"]
    address = msg.text.strip()
    user = msg.from_user

    text = (
        "📨 <b>Заявка на добавление нового зала</b>\n\n"
        f"🏟 Название: <i>{hall_name}</i>\n"
        f"📌 Адрес: <i>{address}</i>\n\n"
        f"👤 Пользователь: <a href='tg://user?id={user.id}'>{user.full_name or user.username or user.id}</a>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔗 Username: @{user.username}" if user.username else ""
    )

    # Шлём всем админам
    for admin_id in ADMINS:
        await msg.bot.send_message(chat_id=admin_id, text=text)

    await msg.answer("🙏 Спасибо! Ваша заявка отправлена администраторам.")
    await state.clear()

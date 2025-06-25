from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from src.states.hall_request_states import HallRequestStates
from src.config import ADMINS
from src.keyboards.back_cancel import back_cancel_kb
from src.models import User
from src.models import SessionLocal

router = Router(name="hall_request")

@router.message(HallRequestStates.waiting_for_hall_name)
async def hall_name_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Добавление зала отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Действие отменено. Вернитесь в меню.", reply_markup=None)
        await state.clear()
        return
    await state.update_data(hall_name=msg.text.strip())
    await msg.answer("Введите адрес зала:", reply_markup=back_cancel_kb())
    await state.set_state(HallRequestStates.waiting_for_hall_address)

@router.message(HallRequestStates.waiting_for_hall_address)
async def hall_address_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Добавление зала отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Введите название зала:", reply_markup=back_cancel_kb())
        await state.set_state(HallRequestStates.waiting_for_hall_name)
        return
    await state.update_data(hall_address=msg.text.strip())
    data = await state.get_data()
    hall_name = data["hall_name"]
    address = data["hall_address"]
    user = msg.from_user
    async with SessionLocal() as session:
        db_user = await session.get(User, user.id)
        fio = db_user.fio if db_user and db_user.fio else user.full_name or user.username or user.id

    text = (
        "📨 <b>Заявка на добавление нового зала</b>\n\n"
        f"🏟 Название: <i>{hall_name}</i>\n"
        f"📌 Адрес: <i>{address}</i>\n\n"
        f"👤 Пользователь: <a href='tg://user?id={user.id}'>{fio}</a>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔗 Username: @{user.username}" if user.username else ""
    )

    # Шлём всем админам
    for admin_id in ADMINS:
        await msg.bot.send_message(chat_id=admin_id, text=text)

    await msg.answer("🙏 Спасибо! Ваша заявка отправлена администраторам.")
    await state.clear()

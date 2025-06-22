from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src.states.hall_states import HallStates
from src.models import SessionLocal
from src.models.hall import Hall
from src.config import ADMINS

router = Router(name="add_hall")

# ───────────── /addhall ───────────────────────────
@router.message(Command("addhall"))
async def cmd_addhall(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMINS:
        await msg.answer("⛔️ Команда только для админов")
        return

    await msg.answer("🏟 Введите название зала:")
    await state.set_state(HallStates.waiting_name)

# ───────────── НАЗВАНИЕ ───────────────────────────
@router.message(HallStates.waiting_name)
async def hall_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await msg.answer("📍 Введите адрес:")
    await state.set_state(HallStates.waiting_address)

# ───────────── АДРЕС  ➜  сохраняем ────────────────
@router.message(HallStates.waiting_address)
async def hall_address(msg: Message, state: FSMContext):
    data = await state.get_data()
    address = msg.text.strip()

    async with SessionLocal() as session:
        hall = Hall(name=data["name"], address=address)   # без price
        session.add(hall)
        await session.commit()

    await msg.answer(
        f"✅ Зал добавлен!\n\n"
        f"<b>{hall.name}</b>\n"
        f"📍 {hall.address}"
    )
    await state.clear()

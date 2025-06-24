import datetime as dt
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from src.states.announce_states import AnnounceStates
from src.states.hall_request_states import HallRequestStates
from src.models import SessionLocal
from src.models.hall import Hall
from src.models.announcement import Announcement
from src.models.user import User
from src.keyboards.halls import halls_keyboard
from src.keyboards.yes_no import yes_no_kb
from src.utils import validators
from src.utils.helpers import local

router = Router()


@router.callback_query(AnnounceStates.waiting_for_hall, F.data == "hall_request_admin")
async def request_new_hall(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❓ Введите, пожалуйста, название вашего зала:")
    await state.set_state(HallRequestStates.waiting_for_hall_name)
    await cb.answer()


@router.message(Command("new"))
async def cmd_new(message: Message, state: FSMContext):
    async with SessionLocal() as session:
        halls = (await session.scalars(select(Hall).order_by(Hall.name))).all()
    if not halls:
        await message.answer("Пока нет ни одного зала. Напишите администратору.")
        return

    await message.answer("Выберите зал:", reply_markup=halls_keyboard(halls))
    await state.set_state(AnnounceStates.waiting_for_hall)


@router.callback_query(AnnounceStates.waiting_for_hall, F.data.startswith("hall_"))
async def hall_chosen(cb: CallbackQuery, state: FSMContext):
    hall_id = int(cb.data.split("_", 1)[1])
    await state.update_data(hall_id=hall_id)

    await cb.message.edit_text("Введите дату тренировки в формате <b>ДД.MM.ГГГГ</b>")
    await state.set_state(AnnounceStates.waiting_for_date)
    await cb.answer()


@router.message(AnnounceStates.waiting_for_date)
async def got_date(msg: Message, state: FSMContext):
    try:
        date_obj = validators.parse_date(msg.text)
    except ValueError as e:
        await msg.reply(str(e))
        return

    await state.update_data(date=date_obj)
    await msg.answer("Введите время тренировки в формате <b>ЧЧ:ММ</b>")
    await state.set_state(AnnounceStates.waiting_for_time)


@router.message(AnnounceStates.waiting_for_time)
async def got_time(msg: Message, state: FSMContext):
    data = await state.get_data()
    try:
        time_obj = validators.parse_time(msg.text)
        validators.future_datetime(data["date"], time_obj)
    except ValueError as e:
        await msg.reply(str(e))
        return

    await state.update_data(time=time_obj)
    await msg.answer("Сколько игроков нужно? Введите <b>число</b>.")
    await state.set_state(AnnounceStates.waiting_for_players_cnt)


@router.message(AnnounceStates.waiting_for_players_cnt)
async def got_players(msg: Message, state: FSMContext):
    try:
        players = validators.is_positive_int(msg.text)
    except ValueError as e:
        await msg.reply(str(e))
        return

    await state.update_data(players=players)
    await msg.answer("Укажите роли (например: «связка, нападающие») или «-»")
    await state.set_state(AnnounceStates.waiting_for_roles)


@router.message(AnnounceStates.waiting_for_roles)
async def got_roles(msg: Message, state: FSMContext):
    await state.update_data(roles=msg.text.strip() or "-")
    await msg.answer("Нужны ли свои мячи?", reply_markup=yes_no_kb)
    await state.set_state(AnnounceStates.waiting_for_balls_needed)


@router.callback_query(AnnounceStates.waiting_for_balls_needed, F.data.in_({"yes", "no"}))
async def balls_answer(cb: CallbackQuery, state: FSMContext):
    await state.update_data(balls_need=(cb.data == "yes"))
    await cb.message.edit_text("Ограничения? (например: «18+», «только мужчины») или «-»")
    await state.set_state(AnnounceStates.waiting_for_restrictions)
    await cb.answer()


@router.message(AnnounceStates.waiting_for_restrictions)
async def got_restr(msg: Message, state: FSMContext):
    await state.update_data(restrictions=msg.text.strip() or "-")
    await msg.answer("Тренировка платная?", reply_markup=yes_no_kb)
    await state.set_state(AnnounceStates.waiting_for_is_paid)


@router.callback_query(AnnounceStates.waiting_for_is_paid, F.data.in_({"yes", "no"}))
async def is_paid_answer(cb: CallbackQuery, state: FSMContext):
    paid = (cb.data == "yes")
    await state.update_data(is_paid=paid)

    data = await state.get_data()
    dt_full = dt.datetime.combine(data["date"], data["time"]).replace(
        tzinfo=validators.MINSK_TZ
    )

    async with SessionLocal() as session:
        # 1) Убедимся, что пользователь есть
        user = await session.get(User, cb.from_user.id)
        if not user:
            user = User(
                id=cb.from_user.id,
                username=cb.from_user.username,
                first_name=cb.from_user.first_name or "",
                last_name=cb.from_user.last_name,
                rating_sum=0,
                rating_votes=0,
                rating=Decimal("5.00"),
            )
            session.add(user)
            await session.flush()

        # 2) Создаём объявление
        ann = Announcement(
            author_id    = user.id,
            hall_id      = data["hall_id"],
            datetime     = dt_full,
            players_need = data["players"],
            roles        = data["roles"],
            balls_need   = data["balls_need"],
            restrictions = data["restrictions"],
            is_paid      = paid,
        )
        session.add(ann)
        await session.commit()
        await session.refresh(ann)

        # Получаем название зала
        hall_name = await session.scalar(select(Hall.name).where(Hall.id == ann.hall_id))

    # Формируем и отправляем текст
    local_dt = local(ann.datetime)
    text = (
        "🏐 <b>Объявление создано</b>\n"
        f"ID: <code>{ann.id}</code>\n"
        f"Зал: {hall_name}\n"
        f"Дата/время: {local_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Нужно игроков: {ann.players_need}\n"
        f"Роли: {ann.roles}\n"
        f"Мячи: {'нужны' if ann.balls_need else 'не нужны'}\n"
        f"Ограничения: {ann.restrictions}\n"
        f"Тип: {'Платная' if ann.is_paid else 'Бесплатная'}"
    )
    await cb.message.edit_text(text)
    await state.clear()
    await cb.answer("Сохранено!")


def render_announcement(ann: Announcement, hall_name: str = None) -> str:
    now = dt.datetime.now(validators.MINSK_TZ)
    local_dt = local(ann.datetime)
    header = "❌ <b>Тренировка прошла</b>\n\n" if ann.datetime <= now else ""
    if hall_name is None:
        hall = getattr(ann, "hall", None)
        hall_name = hall.name if hall else "-"
    return (
        f"{header}"
        "🏐 <b>Объявление</b>\n"
        f"ID: <code>{ann.id}</code>\n"
        f"Зал: {hall_name}\n"
        f"Дата/время: {local_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Нужно игроков: {ann.players_need}\n"
        f"Роли: {ann.roles}\n"
        f"Мячи: {'нужны' if ann.balls_need else 'не нужны'}\n"
        f"Ограничения: {ann.restrictions}\n"
        f"Тип: {'Платная' if ann.is_paid else 'Бесплатная'}"
    )

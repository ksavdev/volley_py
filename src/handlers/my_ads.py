import datetime as dt
from datetime import timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import SessionLocal
from src.models.announcement import Announcement
from src.states.edit_states import EditStates
from src.keyboards.announce_manage import (
    list_keyboard,
    manage_keyboard,
    choose_field_keyboard,
)
from src.utils import validators
from src.utils.helpers import local

router = Router(name="my_ads")


# ───────────── /my — список объявлений ─────────────────────────
@router.message(Command("my"))
async def cmd_my_ads(message: Message):
    author_id = message.from_user.id
    async with SessionLocal() as session:
        ads = (
            await session.scalars(
                select(Announcement)
                .options(selectinload(Announcement.hall))
                .where(Announcement.author_id == author_id)
                .order_by(Announcement.datetime.desc())
            )
        ).all()

    if not ads:
        await message.answer("У вас пока нет объявлений.")
        return

    await message.answer("Ваши объявления:", reply_markup=list_keyboard(ads))


# ───────────── показать/отменить запись на тренировку ────────────
@router.callback_query(F.data.startswith("players_"))
async def show_players(cb: CallbackQuery):
    # делегируем в отдельный модуль
    from src.handlers.my_ads_players import show_players as _show
    await _show(cb)


# ───────────── открыть объявление ──────────────────────────────
@router.callback_query(
    F.data.startswith("myad_")
    & ~F.data.startswith(("myad_del_", "myad_edit_"))
    & (F.data != "myad_back")
)
async def myad_chosen(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[1])
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id, options=[selectinload(Announcement.hall)])
    if not ad or ad.author_id != cb.from_user.id:
        await cb.answer("Объявление не найдено.", show_alert=True)
        return

    info = (
        f"<b>ID:</b> {ad.id}\n"
        f"<b>Зал:</b> {ad.hall.name}\n"
        f"<b>Дата/время:</b> {local(ad.datetime).strftime('%d.%m.%Y %H:%M')}\n"
        f"<b>Нужно игроков:</b> {ad.players_need}\n"
        f"<b>Роли:</b> {ad.roles}\n"
        f"<b>Мячи:</b> {'нужны' if ad.balls_need else 'не нужны'}\n"
        f"<b>Ограничения:</b> {ad.restrictions}\n"
        f"<b>Тип:</b> {'Платная' if ad.is_paid else 'Бесплатная'}"
    )
    await cb.message.edit_text(info, reply_markup=manage_keyboard(ad.id))
    await cb.answer()


# ───────────── удалить объявление ──────────────────────────────
@router.callback_query(F.data.startswith("myad_del_"))
async def myad_delete(cb: CallbackQuery):
    ad_id = int(cb.data.split("_")[2])
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad or ad.author_id != cb.from_user.id:
            await cb.answer("Объявление не найдено.", show_alert=True)
            return
        await session.delete(ad)
        await session.commit()
    await cb.message.edit_text(f"Объявление ID {ad_id} удалено ✅")
    await cb.answer("Удалено!", show_alert=True)


# ───────────── инициировать изменение ──────────────────────────
@router.callback_query(F.data.startswith("myad_edit_"))
async def myad_edit(cb: CallbackQuery, state: FSMContext):
    ad_id = int(cb.data.split("_")[2])
    # проверяем, что тренировка не прошла более часа назад
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
    now = dt.datetime.now(validators.MINSK_TZ)
    if now > ad.datetime + timedelta(hours=1):
        return await cb.answer(
            "⏳ Тренировка прошла более часа назад — редактирование невозможно.",
            show_alert=True
        )

    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
    await state.set_state(EditStates.choosing_field)
    await cb.answer()


# ───────────── выбор поля для редактирования ───────────────────
@router.callback_query(EditStates.choosing_field, F.data.startswith("edit_field_"))
async def choose_field(cb: CallbackQuery, state: FSMContext):
    # edit_field_<field>_<id>
    parts = cb.data.split("_")
    field = parts[2]
    await state.update_data(field=field)

    prompts = {
        "date":     "Введите новую дату <b>ДД.ММ.ГГГГ</b>",
        "time":     "Введите новое время <b>ЧЧ:ММ</b>",
        "players":  "Введите новое количество игроков (число)",
        "roles":    "Введите новые роли или «-»",
        "balls":    "Нужны ли мячи? (да/нет)",
        "restrict": "Введите новые ограничения или «-»",
        "paid":     "Тренировка платная? (да/нет)",
    }
    await cb.message.edit_text(prompts[field])

    mapping = {
        "date":     EditStates.editing_date,
        "time":     EditStates.editing_time,
        "players":  EditStates.editing_players,
        "roles":    EditStates.editing_roles,
        "balls":    EditStates.editing_balls,
        "restrict": EditStates.editing_restrict,
        "paid":     EditStates.editing_is_paid,
    }
    await state.set_state(mapping[field])
    await cb.answer()


# ───────────── общий helper для применения изменений ────────────
async def _apply_edit(cb_msg: Message | CallbackQuery, state: FSMContext, *, new_dt: dt.datetime = None, **fields):
    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await cb_msg.answer("Объявление не найдено.")
            await state.clear()
            return

        if new_dt is not None:
            ad.datetime = new_dt
        else:
            for attr, val in fields.items():
                setattr(ad, attr, val)

        await session.commit()
        await session.refresh(ad)

    await cb_msg.answer("Изменено ✅")
    await state.clear()
    await myad_chosen(cb_msg if isinstance(cb_msg, CallbackQuery) else cb_msg.as_event())


# ─────────────── 1. Изменение ДАТЫ ────────────────────────────
@router.message(EditStates.editing_date)
async def edit_date(msg: Message, state: FSMContext):
    try:
        new_date = validators.parse_date(msg.text)
    except ValueError as e:
        return await msg.reply(str(e))

    data = await state.get_data()
    ad_id = data["ad_id"]
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)

    new_dt = dt.datetime.combine(new_date, ad.datetime.timetz()).replace(
        tzinfo=validators.MINSK_TZ
    )
    await _apply_edit(msg, state, new_dt=new_dt)


# ─────────────── 2. Изменение ВРЕМЕНИ ─────────────────────────
@router.message(EditStates.editing_time)
async def edit_time(msg: Message, state: FSMContext):
    try:
        new_time = validators.parse_time(msg.text)
    except ValueError as e:
        return await msg.reply(str(e))

    data = await state.get_data()
    ad_id = data["ad_id"]
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)

    new_dt = dt.datetime.combine(ad.datetime.date(), new_time).replace(
        tzinfo=validators.MINSK_TZ
    )
    await _apply_edit(msg, state, new_dt=new_dt)


# ─────────────── 3. Изменение КОЛ-ВА ИГРОКОВ ───────────────────
@router.message(EditStates.editing_players)
async def edit_players(msg: Message, state: FSMContext):
    try:
        cnt = validators.is_positive_int(msg.text)
    except ValueError as e:
        return await msg.reply(str(e))
    await _apply_edit(msg, state, players_need=cnt)


# ─────────────── 4. Остальные поля ───────────────────────────
@router.message(EditStates.editing_roles)
async def edit_roles(msg: Message, state: FSMContext):
    await _apply_edit(msg, state, roles=msg.text.strip() or "-")


@router.message(EditStates.editing_balls)
async def edit_balls(msg: Message, state: FSMContext):
    text = msg.text.lower()
    if text not in {"да", "нет"}:
        return await msg.reply("Напишите «да» или «нет».")
    await _apply_edit(msg, state, balls_need=(text == "да"))


@router.message(EditStates.editing_restrict)
async def edit_restrict(msg: Message, state: FSMContext):
    await _apply_edit(msg, state, restrictions=msg.text.strip() or "-")


@router.message(EditStates.editing_is_paid)
async def edit_paid(msg: Message, state: FSMContext):
    text = msg.text.lower()
    if text not in {"да", "нет"}:
        return await msg.reply("Напишите «да» или «нет».")
    await _apply_edit(msg, state, is_paid=(text == "да"))


# ─────────────── Отмена редактирования ─────────────────────────
@router.callback_query(EditStates.choosing_field, F.data == "edit_cancel")
async def edit_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Изменение отменено.")
    await state.clear()
    await cb.answer()

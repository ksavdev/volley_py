import datetime as dt
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
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


# ───────────── открыть объявление ──────────────────────────────
@router.callback_query(F.data.startswith("myad_") & ~F.data.startswith(("myad_del_", "myad_edit_")) & (F.data != "myad_back"))
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
    await cb.answer("Удалено!")


# ───────────── инициировать изменение ──────────────────────────
@router.callback_query(F.data.startswith("myad_edit_"))
async def myad_edit(cb: CallbackQuery, state: FSMContext):
    ad_id = int(cb.data.split("_")[2])
    await state.update_data(ad_id=ad_id)
    await cb.message.edit_text("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
    await state.set_state(EditStates.choosing_field)
    await cb.answer()


# ───────────── выбор поля для редактирования ───────────────────
@router.callback_query(EditStates.choosing_field, F.data.startswith("edit_field_"))
async def choose_field(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")   # edit_field_<name>_<id>
    field = parts[2]
    await state.update_data(field=field)

    prompts = {
        "date":      "Введите новую дату <b>ДД.ММ.ГГГГ</b>",
        "time":      "Введите новое время <b>ЧЧ:ММ</b>",
        "players":   "Введите новое количество игроков (число)",
        "roles":     "Введите новые роли или «-»",
        "balls":     "Нужны ли мячи? (да/нет)",
        "restrict":  "Введите новые ограничения или «-»",
        "paid":      "Тренировка платная? (да/нет)",
    }
    await cb.message.edit_text(prompts[field])
    # переводим в нужный State
    mapping = {
        "date": EditStates.editing_date,
        "time": EditStates.editing_time,
        "players": EditStates.editing_players,
        "roles": EditStates.editing_roles,
        "balls": EditStates.editing_balls,
        "restrict": EditStates.editing_restrict,
        "paid": EditStates.editing_is_paid,
    }
    await state.set_state(mapping[field])
    await cb.answer()


# ───────────── обработчики для каждого поля ────────────────────
async def _apply_edit(cb_msg: Message | CallbackQuery, state: FSMContext, value):
    data = await state.get_data()
    ad_id = data["ad_id"]
    field = data["field"]

    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(Announcement, ad_id)
        if not ad:
            await cb_msg.answer("Объявление не найдено.")
            await state.clear()
            return
        setattr(ad, field_mapping[field], value)
        await session.commit()

    await cb_msg.answer("Изменено ✅")
    await state.clear()

    # показать обновлённое объявление
    await myad_chosen(
        cb_msg if isinstance(cb_msg, CallbackQuery) else cb_msg.as_event(),
    )

field_mapping = {
    "date": "datetime",
    "time": "datetime",
    "players": "players_need",
    "roles": "roles",
    "balls": "balls_need",
    "restrict": "restrictions",
    "paid": "is_paid",
}

# ───────────────────── helper ──────────────────────────
async def _apply_edit(cb_msg: Message | CallbackQuery, state: FSMContext, new_dt: dt.datetime | None = None, **plain):
    """
    new_dt — готовый datetime, используется когда меняем дату/время.
    plain  — поле=значение для остальных случаев.
    """
    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(Announcement, ad_id)
        if not ad:
            await cb_msg.answer("Объявление не найдено.")
            await state.clear()
            return

        if new_dt is not None:
            ad.datetime = new_dt
        else:
            for k, v in plain.items():
                setattr(ad, k, v)

        await session.commit()
        await session.refresh(ad)

    await cb_msg.answer("Изменено ✅")
    await state.clear()
    # показать обновлённую карточку
    await myad_chosen(cb_msg if isinstance(cb_msg, CallbackQuery) else cb_msg.as_event())


# ─────────────── 1. Изменяем ДАТУ ──────────────────────
@router.message(EditStates.editing_date)
async def edit_date(msg: Message, state: FSMContext):
    try:
        new_date = validators.parse_date(msg.text)
    except ValueError as e:
        await msg.reply(str(e)); return

    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(Announcement, ad_id)
        if not ad:
            await msg.reply("Объявление не найдено."); await state.clear(); return
        # комбинируем новую дату со старым временем
        new_dt = dt.datetime.combine(new_date, ad.datetime.timetz())

    await _apply_edit(msg, state, new_dt=new_dt)


# ─────────────── 2. Изменяем ВРЕМЯ ─────────────────────
@router.message(EditStates.editing_time)
async def edit_time(msg: Message, state: FSMContext):
    try:
        new_time = validators.parse_time(msg.text)
    except ValueError as e:
        await msg.reply(str(e)); return

    data = await state.get_data()
    ad_id = data["ad_id"]

    async with SessionLocal() as session:
        ad: Announcement | None = await session.get(Announcement, ad_id)
        if not ad:
            await msg.reply("Объявление не найдено."); await state.clear(); return
        # комбинируем старую дату с новым временем
        new_dt = dt.datetime.combine(ad.datetime.date(), new_time)

    await _apply_edit(msg, state, new_dt=new_dt)


# ─────────────── 3. Остальные поля ─────────────────────
@router.message(EditStates.editing_players)
async def edit_players(msg: Message, state: FSMContext):
    try:
        cnt = validators.is_positive_int(msg.text)
    except ValueError as e:
        await msg.reply(str(e)); return
    await _apply_edit(msg, state, players_need=cnt)


@router.message(EditStates.editing_roles)
async def edit_roles(msg: Message, state: FSMContext):
    await _apply_edit(msg, state, roles=msg.text.strip() or "-")


@router.message(EditStates.editing_balls)
async def edit_balls(msg: Message, state: FSMContext):
    if msg.text.lower() not in {"да", "нет"}:
        await msg.reply("Напишите «да» или «нет»."); return
    await _apply_edit(msg, state, balls_need=(msg.text.lower() == "да"))


@router.message(EditStates.editing_restrict)
async def edit_restrict(msg: Message, state: FSMContext):
    await _apply_edit(msg, state, restrictions=msg.text.strip() or "-")


@router.message(EditStates.editing_is_paid)
async def edit_paid(msg: Message, state: FSMContext):
    if msg.text.lower() not in {"да", "нет"}:
        await msg.reply("Напишите «да» или «нет»."); return
    await _apply_edit(msg, state, is_paid=(msg.text.lower() == "да"))


# ─────────────── Отмена редактирования ─────────────────
@router.callback_query(EditStates.choosing_field, F.data == "edit_cancel")
async def edit_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Изменение отменено.")
    await state.clear()
    await cb.answer()
import datetime as dt
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from src.states.announce_states import AdStates
from src.states.hall_request_states import HallRequestStates
from src.models import SessionLocal
from src.models.hall import Hall
from src.models.announcement import Announcement
from src.models.user import User
from src.keyboards.halls import halls_keyboard
from src.keyboards.common_kb import yes_no_kb, YesNoCallback
from src.keyboards.cancel import cancel_kb
from src.keyboards.back_cancel import back_cancel_kb
from src.utils import validators
from src.keyboards.announce_manage import choose_field_keyboard
from src.handlers.start import whitelist_required


router = Router()


@router.callback_query(AdStates.waiting_for_hall, F.data == "hall_request_admin")
@whitelist_required
async def request_new_hall(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("❓ Введите, пожалуйста, название вашего зала:")
    await state.set_state(HallRequestStates.waiting_for_hall_name)
    await cb.answer()


@router.message(Command("new"))
@whitelist_required
async def cmd_new(message: Message, state: FSMContext):
    async with SessionLocal() as session:
        halls = (await session.scalars(select(Hall).order_by(Hall.name))).all()
    if not halls:
        await message.answer("Пока нет ни одного зала. Напишите администратору.")
        return

    await message.answer("Выберите зал:", reply_markup=halls_keyboard(halls))
    await state.set_state(AdStates.waiting_for_hall)


@router.callback_query(AdStates.waiting_for_hall, F.data.startswith("hall_"))
async def hall_chosen(cb: CallbackQuery, state: FSMContext):
    hall_id = int(cb.data.split("_", 1)[1])
    await state.update_data(hall_id=hall_id)
    await cb.message.answer("Введите дату тренировки в формате <b>ДД.MM.ГГГГ</b>", reply_markup=back_cancel_kb())
    await state.set_state(AdStates.waiting_for_date)
    await cb.answer()


@router.message(AdStates.waiting_for_date)
async def got_date(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Создание объявления отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        async with SessionLocal() as session:
            halls = (await session.scalars(select(Hall).order_by(Hall.name))).all()
        await msg.answer("Выберите зал:", reply_markup=halls_keyboard(halls))
        await state.set_state(AdStates.waiting_for_hall)
        return

    try:
        date_obj = validators.parse_date(msg.text)
    except ValueError as e:
        await msg.reply(f"{e}\n\nПример: 25.06.2025", reply_markup=back_cancel_kb())
        return

    await state.update_data(date=date_obj)
    await msg.answer("Введите время тренировки в формате <b>ЧЧ:ММ</b>", reply_markup=back_cancel_kb())
    await state.set_state(AdStates.waiting_for_time)


@router.message(AdStates.waiting_for_time)
async def got_time(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Создание объявления отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Введите дату тренировки в формате <b>ДД.MM.ГГГГ</b>", reply_markup=back_cancel_kb())
        await state.set_state(AdStates.waiting_for_date)
        return

    data = await state.get_data()
    try:
        time_obj = validators.parse_time(msg.text)
        validators.future_datetime(data["date"], time_obj)
    except ValueError as e:
        await msg.reply(f"{e}\n\nПример: 19:00", reply_markup=back_cancel_kb())
        return

    await state.update_data(time=time_obj)
    await msg.answer("Сколько игроков нужно? Введите <b>число</b>.", reply_markup=back_cancel_kb())
    await state.set_state(AdStates.waiting_for_players_cnt)


@router.message(AdStates.waiting_for_players_cnt)
async def got_players(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Создание объявления отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Введите время тренировки в формате <b>ЧЧ:ММ</b>", reply_markup=back_cancel_kb())
        await state.set_state(AdStates.waiting_for_time)
        return

    try:
        players = validators.is_positive_int(msg.text)
    except ValueError as e:
        await msg.reply(f"{e}\n\nПример: 12", reply_markup=back_cancel_kb())
        return

    await state.update_data(players=players)
    await msg.answer("Укажите роли (например: «связка, нападающие») или «-»", reply_markup=back_cancel_kb())
    await state.set_state(AdStates.waiting_for_roles)


@router.message(AdStates.waiting_for_roles)
async def got_roles(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Создание объявления отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Сколько игроков нужно? Введите <b>число</b>.", reply_markup=back_cancel_kb())
        await state.set_state(AdStates.waiting_for_players_cnt)
        return

    await state.update_data(roles=msg.text.strip() or "-")
    await msg.answer("Нужны ли свои мячи?", reply_markup=yes_no_kb())
    await state.set_state(AdStates.waiting_for_balls_needed)


@router.callback_query(AdStates.waiting_for_balls_needed, YesNoCallback.filter())
async def balls_answer(cb: CallbackQuery, callback_data: YesNoCallback, state: FSMContext):
    await state.update_data(balls_need=(callback_data.answer == "yes"))
    await cb.message.answer("Ограничения? (например: «18+», «только мужчины») или «-»", reply_markup=back_cancel_kb())
    await state.set_state(AdStates.waiting_for_restrictions)
    await cb.answer()


@router.message(AdStates.waiting_for_restrictions)
async def got_restr(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Создание объявления отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Нужны ли свои мячи?", reply_markup=yes_no_kb())
        await state.set_state(AdStates.waiting_for_balls_needed)
        return

    await state.update_data(restrictions=msg.text.strip() or "-")
    await msg.answer("Тренировка платная?", reply_markup=yes_no_kb())
    await state.set_state(AdStates.waiting_for_is_paid)


@router.message(AdStates.waiting_for_is_paid)
async def waiting_for_price(msg: Message, state: FSMContext):
    # Этот хендлер нужен только для ручного перехода, если пользователь напишет текст вместо кнопки
    await msg.answer("Пожалуйста, выберите вариант с помощью кнопок.", reply_markup=yes_no_kb())


@router.callback_query(AdStates.waiting_for_is_paid, YesNoCallback.filter())
async def is_paid_answer(cb: CallbackQuery, callback_data: YesNoCallback, state: FSMContext):
    paid = (callback_data.answer == "yes")
    await state.update_data(is_paid=paid)
    if paid:
        await cb.message.answer("Введите цену тренировки в рублях (только число):", reply_markup=back_cancel_kb())
        await state.set_state(AdStates.waiting_for_price)
    else:
        await finish_announcement(cb, state, price=None)
    await cb.answer()


@router.message(AdStates.waiting_for_price)
async def got_price(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Создание объявления отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        await msg.answer("Тренировка платная?", reply_markup=yes_no_kb())
        await state.set_state(AdStates.waiting_for_is_paid)
        return
    try:
        price = int(msg.text.strip())
        if price <= 0:
            raise ValueError
    except Exception:
        await msg.reply("Введите положительное число (стоимость в рублях).", reply_markup=back_cancel_kb())
        return
    await finish_announcement(msg, state, price=price)


async def finish_announcement(event, state: FSMContext, price: int | None):
    # event: Message или CallbackQuery
    data = await state.get_data()
    dt_full = validators.combine_date_time_with_tz(data["date"], data["time"])
    dt_full = validators.to_naive_datetime(dt_full)
    async with SessionLocal() as session:
        user = await session.get(User, event.from_user.id)
        if not user:
            user = User(
                id=event.from_user.id,
                username=event.from_user.username,
                first_name=event.from_user.first_name or "",
                last_name=event.from_user.last_name,
                rating_sum=0,
                rating_votes=0,
                rating=Decimal("5.00"),
            )
            session.add(user)
            await session.flush()
        ann = Announcement(
            author_id    = user.id,
            hall_id      = data["hall_id"],
            datetime     = dt_full,
            capacity     = data["players"],
            roles        = data["roles"],
            balls_need   = data["balls_need"],
            restrictions = data["restrictions"],
            is_paid      = data["is_paid"],
            price        = price if data["is_paid"] else None,
        )
        session.add(ann)
        await session.commit()
        await session.refresh(ann)
        hall_name = await session.scalar(select(Hall.name).where(Hall.id == ann.hall_id))
    text = (
        "🏐 <b>Объявление создано</b>\n"
        f"ID: <code>{ann.id}</code>\n"
        f"Зал: {hall_name}\n"
        f"Дата/время: {ann.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        f"Нужно игроков: {ann.capacity}\n"
        f"Роли: {ann.roles}\n"
        f"Мячи: {'нужны' if ann.balls_need else 'не нужны'}\n"
        f"Ограничения: {ann.restrictions}\n"
        f"Тип: {'Платная' if ann.is_paid else 'Бесплатная'}"
        + (f"\n💰 Цена: {ann.price} руб." if ann.is_paid and ann.price else "")
    )
    if hasattr(event, "message"):
        await event.message.edit_text(text)
    else:
        await event.answer(text)
    await state.clear()
    if hasattr(event, "answer"):
        await event.answer("Сохранено!")


def render_announcement(ann: Announcement, hall_name: str = None) -> str:
    # Приводим обе даты к naive для корректного сравнения
    now = dt.datetime.now(validators.MINSK_TZ).replace(tzinfo=None)
    ann_dt = ann.datetime
    if ann_dt.tzinfo is not None:
        ann_dt = ann_dt.replace(tzinfo=None)
    header = "❌ <b>Тренировка прошла</b>\n\n" if ann_dt <= now else ""
    if hall_name is None:
        hall = getattr(ann, "hall", None)
        hall_name = hall.name if hall else "-"
    return (
        f"{header}"
        "🏐 <b>Объявление</b>\n"
        f"ID: <code>{ann.id}</code>\n"
        f"Зал: {hall_name}\n"
        f"Дата/время: {ann.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        f"Нужно игроков: {ann.capacity}\n"
        f"Роли: {ann.roles}\n"
        f"Мячи: {'нужны' if ann.balls_need else 'не нужны'}\n"
        f"Ограничения: {ann.restrictions}\n"
        f"Тип: {'Платная' if ann.is_paid else 'Бесплатная'}"
        + (f"\n💰 Цена: {ann.price} руб." if ann.is_paid and ann.price else "")
    )


@router.callback_query(F.data.startswith("delete_ad_"))
@whitelist_required
async def delete_ad(cb: CallbackQuery):
    ann_id = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        ann = await session.get(Announcement, ann_id)
        now = dt.datetime.now(validators.MINSK_TZ).replace(tzinfo=None)
        if ann.datetime < now:
            await cb.message.answer("Нельзя удалять прошедшие тренировки!")
            return
        session.delete(ann)
        await session.commit()

    await cb.message.answer("Объявление удалено.", reply_markup=None)
    await cb.answer()


@router.callback_query(F.data.startswith("halls_page_"))
async def halls_page(cb: CallbackQuery, state: FSMContext):
    page = int(cb.data.split("_")[-1])
    async with SessionLocal() as session:
        halls = (await session.scalars(select(Hall).order_by(Hall.name))).all()
    await cb.message.edit_text("Выберите зал:", reply_markup=halls_keyboard(halls, page=page))
    await cb.answer()


@router.message(AdStates.editing_date)
async def editing_date_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return
    try:
        new_date = validators.parse_date(msg.text)
    except ValueError as e:
        await msg.reply(f"{e}\n\nПример: 28.06.2025")
        return

    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        # Меняем только дату, время оставляем прежним, tzinfo сохраняем
        new_dt = ad.datetime.replace(year=new_date.year, month=new_date.month, day=new_date.day)
        if new_dt.tzinfo is None:
            new_dt = new_dt.replace(tzinfo=validators.MINSK_TZ)
        ad.datetime = new_dt
        await session.commit()
    await msg.answer("Дата успешно изменена ✅")
    await state.clear()


@router.message(AdStates.editing_time)
async def editing_time_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return
    try:
        new_time = validators.parse_time(msg.text)
    except ValueError as e:
        await msg.reply(f"{e}\n\nПример: 19:00")
        return

    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        # Меняем только время, дату оставляем прежней, tzinfo сохраняем
        new_dt = ad.datetime.replace(hour=new_time.hour, minute=new_time.minute)
        if new_dt.tzinfo is None:
            new_dt = new_dt.replace(tzinfo=validators.MINSK_TZ)
        ad.datetime = new_dt
        await session.commit()
    await msg.answer("Время успешно изменено ✅")
    await state.clear()


@router.message(AdStates.editing_players)
async def editing_players_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return
    try:
        players = validators.is_positive_int(msg.text)
    except ValueError as e:
        await msg.reply(f"{e}\n\nПример: 12")
        return

    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        ad.capacity = players
        await session.commit()
    await msg.answer("Количество игроков успешно изменено ✅")
    await state.clear()


@router.message(AdStates.editing_roles)
async def editing_roles_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return

    roles = msg.text.strip() or "-"
    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        ad.roles = roles
        await session.commit()
    await msg.answer("Роли успешно изменены ✅")
    await state.clear()


@router.message(AdStates.editing_balls)
async def editing_balls_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return

    answer = msg.text.strip().lower()
    if answer not in ("да", "нет"):
        await msg.reply("Введите «да» или «нет».")
        return
    balls_need = (answer == "да")
    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        ad.balls_need = balls_need
        await session.commit()
    await msg.answer("Параметр «Мячи нужны» успешно изменён ✅")
    await state.clear()


@router.message(AdStates.editing_restrict)
async def editing_restrict_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return

    restrictions = msg.text.strip() or "-"
    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        ad.restrictions = restrictions
        await session.commit()
    await msg.answer("Ограничения успешно изменены ✅")
    await state.clear()


@router.message(AdStates.editing_paid)
async def editing_paid_step(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await msg.answer("Редактирование отменено.", reply_markup=None)
        await state.clear()
        return
    if msg.text == "⬅️ Назад":
        data = await state.get_data()
        ad_id = data.get("ad_id")
        await msg.answer("Что изменить?", reply_markup=choose_field_keyboard(ad_id))
        await state.set_state(AdStates.choosing_field)
        return

    answer = msg.text.strip().lower()
    if answer not in ("да", "нет"):
        await msg.reply("Введите «да» или «нет».")
        return
    is_paid = (answer == "да")
    data = await state.get_data()
    ad_id = data.get("ad_id")
    async with SessionLocal() as session:
        ad = await session.get(Announcement, ad_id)
        if not ad:
            await msg.answer("Объявление не найдено.")
            await state.clear()
            return
        now = dt.datetime.now(validators.MINSK_TZ)
        if ad.datetime <= now:
            await msg.answer("Нельзя изменять прошедшие тренировки.")
            await state.clear()
            return
        ad.is_paid = is_paid
        await session.commit()
    await msg.answer("Тип тренировки успешно изменён ✅")
    await state.clear()
    await msg.answer("Тип тренировки успешно изменён ✅")
    await state.clear()
    await msg.answer("Тип тренировки успешно изменён ✅")
    await state.clear()
    await state.clear()

from decimal import Decimal
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand, InlineKeyboardMarkup
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram import Bot
from src.config import ADMINS, is_zbt_enabled_db  # Импорт только здесь
from src.models import SessionLocal
from src.models.user import User
from src.keyboards.main_menu import main_menu_kb
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from functools import wraps

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_fio = State()
    waiting_for_phone = State()

def whitelist_required(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        uid = getattr(event, "from_user", None)
        if uid is None:
            return await handler(event, *args, **kwargs)
        user_id = uid.id
        print(f"[whitelist_required] user_id={user_id}, ADMINS={ADMINS}")  # DEBUG
        if int(user_id) in ADMINS:  # Явно приводим к int
            return await handler(event, *args, **kwargs)
        zbt_enabled = await is_zbt_enabled_db()
        if not zbt_enabled:
            return await handler(event, *args, **kwargs)
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if not user or not user.is_whitelisted:
                if hasattr(event, "answer"):
                    await event.answer("Доступ только для участников закрытого тестирования.", show_alert=True)
                else:
                    await event.reply("Доступ только для участников закрытого тестирования.")
                return
        return await handler(event, *args, **kwargs)
    return wrapper

@router.message(CommandStart())
@whitelist_required
async def on_start(message: Message, state: FSMContext):
    tg_user = message.from_user
    tg_id = tg_user.id
    username = tg_user.username
    first_name = tg_user.first_name or ""
    last_name = tg_user.last_name

    async with SessionLocal() as session:
        db_user = await session.get(User, tg_id)
        if db_user is None:
            user = User(
                id=tg_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                rating_sum=0,
                rating_votes=0,
            )
            session.add(user)
            await session.commit()
            db_user = user
        else:
            db_user.username = username
            db_user.first_name = first_name
            db_user.last_name = last_name
            await session.commit()

        # Проверяем регистрацию
        if not db_user.fio:
            await message.answer("Пожалуйста, введите ваши ФИО (например: Иванов Иван Иванович):")
            await state.set_state(RegistrationStates.waiting_for_fio)
            return
        if not db_user.phone:
            await message.answer("Пожалуйста, введите ваш номер телефона в формате +375291234567:")
            await state.set_state(RegistrationStates.waiting_for_phone)
            return

    text = (
        f"👋 Привет, {db_user.fio or first_name or 'игрок'}!\n\n"
        "Я помогу найти или создать тренировку по волейболу в Минске.\n"
        "Выберите действие из меню ниже 👇"
    )
    print(f"[DEBUG] ADMINS={ADMINS}, your_id={message.from_user.id}")  # временно для отладки
    # Убираем ReplyKeyboardMarkup, показываем InlineKeyboardMarkup
    inline_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать объявление", callback_data="menu_new")],
        [InlineKeyboardButton(text="📋 Мои объявления", callback_data="menu_my")],
        [InlineKeyboardButton(text="🔍 Найти тренировку", callback_data="menu_search")],
        [InlineKeyboardButton(text="📝 Мои заявки", callback_data="menu_requests")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile")],
    ])
    await message.answer(text, reply_markup=inline_menu)

    from aiogram import Bot
    bot: Bot = message.bot

    # Устанавливаем команды для меню в зависимости от роли
    if message.from_user.id in ADMINS:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="new", description="Создать объявление"),
            BotCommand(command="my", description="Мои объявления"),
            BotCommand(command="search", description="Найти тренировку"),
            BotCommand(command="requests", description="Мои заявки"),
            BotCommand(command="addhall", description="Добавить зал"),
            BotCommand(command="dm", description="Писать пользователю"),
            BotCommand(command="whitelist", description="Добавить в whitelist"),
            BotCommand(command="unwhitelist", description="Убрать из whitelist"),
            BotCommand(command="zbt_on", description="Включить ЗБТ (только whitelist)"),
            BotCommand(command="zbt_off", description="Выключить ЗБТ (открыто для всех)"),
        ], scope={"type": "chat", "chat_id": message.from_user.id})
    else:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="new", description="Создать объявление"),
            BotCommand(command="my", description="Мои объявления"),
            BotCommand(command="search", description="Найти тренировку"),
            BotCommand(command="requests", description="Мои заявки"),
            BotCommand(command="profile", description="Мой профиль"),
        ], scope={"type": "chat", "chat_id": message.from_user.id})

@router.message(Command("start"))
@whitelist_required
async def cmd_start(msg: Message, bot: Bot):
    if msg.from_user.id in ADMINS:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="new", description="Создать объявление"),
            BotCommand(command="my", description="Мои объявления"),
            BotCommand(command="search", description="Найти тренировку"),
            BotCommand(command="requests", description="Мои заявки"),
            BotCommand(command="addhall", description="Добавить зал"),
            BotCommand(command="dm", description="Писать пользователю"),
            BotCommand(command="whitelist", description="Добавить в whitelist"),
            BotCommand(command="unwhitelist", description="Убрать из whitelist"),
            BotCommand(command="zbt_on", description="Включить ЗБТ (только whitelist)"),
            BotCommand(command="zbt_off", description="Выключить ЗБТ (открыто для всех)"),
        ], scope={"type": "chat", "chat_id": msg.from_user.id})
    else:
        await bot.set_my_commands([
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="new", description="Создать объявление"),
            BotCommand(command="my", description="Мои объявления"),
            BotCommand(command="search", description="Найти тренировку"),
            BotCommand(command="requests", description="Мои заявки"),
        ], scope={"type": "chat", "chat_id": msg.from_user.id})

@router.callback_query(lambda c: c.data == "menu_new")
@whitelist_required
async def menu_new_callback(cb: CallbackQuery, state: FSMContext):
    # Вместо вызова cmd_new(cb.message, ...) — сразу запускайте бизнес-логику здесь!
    # Например, скопируйте нужный код из cmd_new или вынесите бизнес-логику в отдельную функцию.
    from src.models.hall import Hall
    from src.keyboards.halls import halls_keyboard
    from src.states.announce_states import AdStates
    from sqlalchemy import select
    async with SessionLocal() as session:
        halls = (await session.scalars(select(Hall).order_by(Hall.name))).all()
    if not halls:
        await cb.message.answer("Пока нет ни одного зала. Напишите администратору.")
        await cb.answer()
        return
    await cb.message.answer("Выберите зал:", reply_markup=halls_keyboard(halls))
    await state.set_state(AdStates.waiting_for_hall)
    await cb.answer()

@router.callback_query(lambda c: c.data == "menu_my")
@whitelist_required
async def menu_my_callback(cb: CallbackQuery):
    from src.handlers.my_ads import cmd_my_ads
    await cmd_my_ads(cb)  # <-- передаём сам CallbackQuery, а не cb.message
    await cb.answer()

@router.callback_query(lambda c: c.data == "menu_search")
@whitelist_required
async def menu_search_callback(cb: CallbackQuery):
    # Импортируем только бизнес-логику, не message-хендлер!
    from src.handlers.search import search_menu_kb
    await cb.message.answer("Выберите тип тренировки:", reply_markup=search_menu_kb())
    await cb.answer()

@router.callback_query(lambda c: c.data == "menu_requests")
@whitelist_required
async def menu_requests_callback(cb: CallbackQuery):
    from src.handlers.my_signups import cmd_requests_callback
    await cmd_requests_callback(cb)
    await cb.answer()

@router.callback_query(lambda c: c.data == "menu_profile")
@whitelist_required
async def menu_profile_callback(cb: CallbackQuery):
    from src.handlers.profile import cmd_profile
    # Создаём временный Message с нужным from_user (или просто прокидываем cb)
    await cmd_profile(cb)
    await cb.answer()

@router.message(RegistrationStates.waiting_for_fio)
async def reg_fio(msg: Message, state: FSMContext):
    fio = msg.text.strip()
    if len(fio.split()) < 2:
        await msg.answer("Введите ФИО полностью (например: Иванов Иван Иванович):")
        return
    async with SessionLocal() as session:
        user = await session.get(User, msg.from_user.id)
        if user:
            user.fio = fio
            await session.commit()
    await msg.answer("Спасибо! Теперь введите ваш номер телефона в формате +375291234567:")
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone)
async def reg_phone(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    if not phone.startswith("+375") or not phone[1:].isdigit() or len(phone) != 13:
        await msg.answer("Введите номер в формате +375291234567:")
        return
    async with SessionLocal() as session:
        user = await session.get(User, msg.from_user.id)
        if user:
            user.phone = phone
            await session.commit()
    await msg.answer("Регистрация завершена! Теперь вы можете пользоваться ботом.")
    # Показываем только inline-меню, без main_menu_kb
    inline_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать объявление", callback_data="menu_new")],
        [InlineKeyboardButton(text="📋 Мои объявления", callback_data="menu_my")],
        [InlineKeyboardButton(text="🔍 Найти тренировку", callback_data="menu_search")],
        [InlineKeyboardButton(text="📝 Мои заявки", callback_data="menu_requests")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile")],
    ])
    await msg.answer(
        "Выберите действие из меню ниже 👇",
        reply_markup=inline_menu
    )
    await state.clear()

@router.message(Command("profile"))
@whitelist_required
async def cmd_profile(msg: Message):
    from src.handlers.profile import cmd_profile
    await cmd_profile(msg)
async def cmd_profile(msg: Message):
    from src.handlers.profile import cmd_profile
    await cmd_profile(msg)
    

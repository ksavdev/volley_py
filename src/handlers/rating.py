from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from src.states.rating_states import RatingStates
from src.keyboards.rating import rating_kb
from src.models import SessionLocal
from src.models.user import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.models.announcement import Announcement
from src.models.signup import Signup, SignupStatus
from src.utils.validators import MINSK_TZ
try:
    import redis.asyncio as aioredis
    _redis_available = True
except ModuleNotFoundError:
    print(
        "⚠️ Модуль 'redis' не установлен. "
        "Функция напоминаний о рейтинге не будет работать.\n"
        "Установите его командой: pip install redis>=4.2.0"
    )
    _redis_available = False
import datetime as dt
from aiogram.fsm.state import State, StatesGroup

router = Router(name="rating")

class MultiRatingStates(StatesGroup):
    waiting_for_ratings = State()

@router.message(RatingStates.waiting_for_rating)
async def get_rating(msg: Message, state: FSMContext):
    if msg.text == "❌ Пропустить":
        await msg.answer("Спасибо! Оценка пропущена.")
        await state.clear()
        return
    if not msg.text.startswith("⭐️"):
        await msg.answer("Поставьте оценку от 1 до 5.", reply_markup=rating_kb())
        return
    try:
        rating = int(msg.text.replace("⭐️", "").strip())
        if not (1 <= rating <= 5):
            raise ValueError
    except Exception:
        await msg.answer("Поставьте оценку от 1 до 5.", reply_markup=rating_kb())
        return

    data = await state.get_data()
    user_id = data["rate_user_id"]
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if user:
            user.rating_sum += rating
            user.rating_votes += 1
            await session.commit()
    await msg.answer("Спасибо за вашу оценку!")
    await state.clear()

@router.message(MultiRatingStates.waiting_for_ratings)
async def get_multi_rating(msg: Message, state: FSMContext):
    data = await state.get_data()
    ratings_list = data.get("ratings_list", [])
    current_index = data.get("current_index", 0)
    my_id = data.get("my_id")
    if msg.text == "❌ Пропустить":
        pass  # Просто пропускаем оценку
    else:
        try:
            rating = int(msg.text.replace("⭐️", "").strip())
            if not (1 <= rating <= 5):
                raise ValueError
        except Exception:
            await msg.answer("Поставьте оценку от 1 до 5.", reply_markup=rating_kb())
            return
        rate_user_id = ratings_list[current_index]["user_id"]
        async with SessionLocal() as session:
            user = await session.get(User, rate_user_id)
            if user:
                user.rating_sum += rating
                user.rating_votes += 1
                await session.commit()
    current_index += 1
    if current_index >= len(ratings_list):
        await msg.answer("Спасибо! Все оценки сохранены.")
        await state.clear()
        return
    next_user = ratings_list[current_index]
    await state.update_data(current_index=current_index)
    await msg.answer(
        f"Оцените игрока: <b>{next_user['name']}</b>",
        reply_markup=rating_kb()
    )

async def send_rating_requests(bot):
    if not _redis_available:
        print("⚠️ Redis не доступен, пропускаем отправку напоминаний о рейтинге.")
        return
    try:
        now = dt.datetime.now(MINSK_TZ)
        print(f"[RATING] Запуск задачи напоминаний о рейтинге: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        # Интервал для поиска: 2 часа назад ± 5 минут
        target_time = now - dt.timedelta(hours=2)
        interval_start = target_time - dt.timedelta(minutes=5)
        interval_end = target_time + dt.timedelta(minutes=5)

        # Redis-кэш для предотвращения дублей
        redis = await aioredis.from_url("redis://localhost")
        async with SessionLocal() as session:
            anns = (await session.scalars(
                select(Announcement)
                .where(
                    Announcement.datetime.between(interval_start, interval_end)
                )
                .options(selectinload(Announcement.signups))
            )).all()
            for ann in anns:
                redis_key = f"ratings_sent:{ann.id}"
                already_sent = await redis.get(redis_key)
                if already_sent:
                    print(f"[RATING] Уже отправляли напоминание для объявления {ann.id}")
                    continue
                players = [s.player for s in ann.signups if s.status == SignupStatus.accepted]
                notified_players = []
                for player in players:
                    others = [
                        {"user_id": p.id, "name": p.fio or f"{p.first_name} {p.last_name or ''}".strip()}
                        for p in players if p.id != player.id
                    ]
                    if not others:
                        continue
                    state_data = {
                        "ratings_list": others,
                        "current_index": 0,
                        "my_id": player.id,
                    }
                    await bot.send_message(
                        player.id,
                        f"Тренировка {ann.hall.name} {local(ann.datetime).strftime('%d.%m %H:%M')} завершилась!\n\n"
                        "Пожалуйста, оцените других участников тренировки.",
                        reply_markup=rating_kb()
                    )
                    # FSM состояние
                    from aiogram.fsm.storage.memory import MemoryStorage
                    storage = bot.dispatcher.storage if hasattr(bot, "dispatcher") else MemoryStorage()
                    await storage.set_data(bot=bot, chat_id=player.id, user_id=player.id, data=state_data)
                    await storage.set_state(bot=bot, chat_id=player.id, user_id=player.id, state=MultiRatingStates.waiting_for_ratings)
                    notified_players.append(player.id)
                # Установить флаг на 1 день
                await redis.set(redis_key, "1", ex=86400)
                print(f"[RATING] Напоминание отправлено по объявлению {ann.id} ({ann.hall.name} {local(ann.datetime).strftime('%d.%m %H:%M')}) игрокам: {notified_players}")
        await redis.close()
    except Exception as e:
        print(f"send_rating_requests error: {e}")
        import traceback
        traceback.print_exc()
        traceback.print_exc()

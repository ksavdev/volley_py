from aiogram import Router, F
from aiogram.types import Message
from src.handlers.search import cmd_search
from src.handlers.my_ads import cmd_my_ads
from src.handlers.my_signups import cmd_requests
from src.handlers.add_hall import cmd_addhall
from src.handlers.admin import start_dm

router = Router()

@router.message(F.text == "🔍 Поиск тренировки")
async def menu_search(msg: Message):
    await cmd_search(msg)

@router.message(F.text == "📋 Мои объявления")
async def menu_my_ads(msg: Message):
    await cmd_my_ads(msg)

@router.message(F.text == "📝 Мои заявки")
async def menu_my_requests(msg: Message):
    await cmd_requests(msg)

# Для админов:
@router.message(F.text == "➕ Добавить зал")
async def menu_add_hall(msg: Message, state):
    await cmd_addhall(msg, state)

@router.message(F.text == "✉️ Написать пользователю")
async def menu_dm(msg: Message, state):
    await start_dm(msg, state)
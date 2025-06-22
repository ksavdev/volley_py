from aiogram import Router
from . import (
    start, announce, my_ads, search, confirm,
    my_signups, my_ads_players, add_hall   # ← роутер игроков
)
from aiogram.types import CallbackQuery

router = Router()
router.include_router(start.router)
router.include_router(announce.router)
router.include_router(my_ads.router)
router.include_router(search.router)
router.include_router(confirm.router)
router.include_router(my_signups.router)
router.include_router(my_ads_players.router)
router.include_router(add_hall.router)

@router.callback_query()
async def debug_any_callback(c: CallbackQuery):
    await c.answer(f"DEBUG: {c.data}", show_alert=True)
